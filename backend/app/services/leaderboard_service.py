import uuid

from typing import Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import desc, func

from app.extensions import db
from app.models.game.leaderboard import Leaderboard
from app.models.game.leaderboard_entry import LeaderboardEntry
from app.models.game.user_game_stats.model import UserGameStats
from app.models.user.model import User


class LeaderboardService:
    """Service for managing leaderboards"""

    @staticmethod
    def update_user_rakings(user_id: uuid.UUID, game_id: Optional[uuid.UUID] = None):
        """Update user's rankings across all relevant leaderboards"""
        # Find all active leaderboards for this game
        query = Leaderboard.query.filter_by(is_active=True)

        if game_id:
            query = query.filter(
                db.or_(Leaderboard.game_id == game_id, Leaderboard.game_id.is_(None))
            )

        leaderboards: list[Leaderboard] = query.all()

        for leaderboard in leaderboards:
            if leaderboard.game_id:
                LeaderboardService._update_leaderboard_entry(
                    leaderboard, user_id, game_id=leaderboard.game_id
                )

    @staticmethod
    def _update_leaderboard_entry(
        leaderboard: Leaderboard, user_id: uuid.UUID, game_id: uuid.UUID
    ):
        """Update a specific leaderboard entry for a user"""

        # Calculate score based on ranking criteria
        score_value = LeaderboardService._calculate_score(
            user_id=user_id,
            game_id=game_id,
            ranking_criteria=leaderboard.ranking_criteria,
        )

        if score_value is None:
            return  # User doesn't qualify

        # Get time period boundaries
        period_start, period_end = LeaderboardService._get_period_boundaries(
            time_period=leaderboard.time_period
        )

        # Find or create entry
        entry: LeaderboardEntry | None = LeaderboardEntry.query.filter_by(
            leaderboard_id=leaderboard.id, user_id=user_id, period_start=period_start
        ).first()

        if not entry:
            entry = LeaderboardEntry(
                leaderboard_id=leaderboard.id,
                user_id=user_id,
                period_start=period_start,
                period_end=period_end,
                score_value=score_value,
                rank=0,
            )
            db.session.add(entry)
        else:
            entry.score_value = score_value
            entry.last_updated = datetime.now(timezone.utc)

        # Get games played count
        if leaderboard.game_id:
            stats = UserGameStats.query.filter_by(
                user_id=user_id, game_id=leaderboard.game
            ).first()
            entry.games_played = stats.games_completed if stats else 0
        else:
            # Global leaderboard
            entry.games_played = (
                db.session.query(func.sum(UserGameStats.games_completed))
                .filter_by(user_id=user_id)
                .scalar()
                or 0
            )

        db.session.commit()

        LeaderboardService._recalculate_ranks(
            leaderboard_id=leaderboard.id, period_start=period_start
        )

    @staticmethod
    def _calculate_score(
        user_id: uuid.UUID, game_id: uuid.UUID, ranking_criteria: dict[str, Any]
    ):
        """Calculate score based on ranking criteria"""

        criteria_type = ranking_criteria.get("type")

        if criteria_type == "total_xp":
            # Global XP
            user: User | None = User.query.get(user_id)
            return float(user.total_xp) if user else None

        elif criteria_type == "game_xp":
            # Game-specific XP
            stats = UserGameStats.query.filter_by(
                user_id=user_id, game_id=game_id
            ).first()

            if not stats:
                return None

            min_games = ranking_criteria.get("min_games", 0)
            if stats.games_completed < min_games:
                return None

            return float(stats.total_xp_earned)

        elif criteria_type == "best_score":
            # Best score in a game
            stats = UserGameStats.query.filter_by(
                user_id=user_id,
                game_id=game_id,
            ).first()

            if not stats:
                return None

            min_games = ranking_criteria.get("min_games", 0)
            if stats.games_completed < min_games:
                return None

            return stats.best_score

        elif criteria_type == "average_score":
            # Average score
            stats = UserGameStats.query.filter_by(
                user_id=user_id, game_id=game_id
            ).first()

            if not stats:
                return None

            min_games = ranking_criteria.get("min_games", 5)
            if stats.games_completed < min_games:
                return None

            return stats.average_score

        elif criteria_type == "games_completed":
            # Total games completed
            stats = UserGameStats.query.filter_by(
                user_id=user_id, game_id=game_id
            ).first()

            return float(stats.games_completed) if stats else None

        return None

    @staticmethod
    def _get_period_boundaries(time_period):
        """Get start and end datetime for a time period"""

        now = datetime.now(timezone.utc)

        if time_period == "all_time":
            return datetime(2026, 1, 1), None

        elif time_period == "daily":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            return start, end

        elif time_period == "weekly":
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
            return start, end

        elif time_period == "monthly":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Next month
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
            return start, end

        return now, None

    @staticmethod
    def _recalculate_ranks(leaderboard_id: uuid.UUID, period_start: datetime):
        """Recalculate ranks for all entries in a leaderboard period"""

        entries: list[LeaderboardEntry] = (
            LeaderboardEntry.query.filter_by(
                leaderboard_id=leaderboard_id, period_start=period_start
            )
            .order_by(desc(LeaderboardEntry.score_value))
            .all()
        )

        for idx, entry in enumerate(entries, start=1):
            entry.rank = idx

        db.session.commit()

    @staticmethod
    def get_leaderboard(leaderboard_id: uuid.UUID, limit=100, offset=0):
        """Get leaderboard entries"""

        leaderboard: Leaderboard | None = Leaderboard.query.get(leaderboard_id)
        if not leaderboard:
            return None, "Leaderboard not found"

        period_start, _ = LeaderboardService._get_period_boundaries(
            time_period=leaderboard.time_period
        )

        entries: list[LeaderboardEntry] = (
            LeaderboardEntry.query.filter_by(
                leaderboard_id=leaderboard_id, period_start=period_start
            )
            .order_by(LeaderboardEntry.rank)
            .limit(limit)
            .offset(offset)
            .all()
        )

        return entries, None

    @staticmethod
    def get_user_rank(leaderboard_id: uuid.UUID, user_id: uuid.UUID):
        """Get a specific user's rank on a leaderboard"""

        leaderboard: Leaderboard | None = Leaderboard.query.get(leaderboard_id)
        if not leaderboard:
            return None

        period_start, _ = LeaderboardService._get_period_boundaries(
            time_period=leaderboard.time_period
        )

        entry = LeaderboardEntry.query.filter_by(
            leaderboard_id=leaderboard_id, user_id=user_id, period_start=period_start
        ).first()

        return entry
