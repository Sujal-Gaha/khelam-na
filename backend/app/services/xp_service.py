import uuid

from datetime import datetime, timezone
from typing import Any, Optional, TypedDict

from app.extensions import db
from app.models.game import XPTransaction, XPTransactionTypeEnum
from app.models.game.session.model import GameSession
from app.models.game.user_game_stats.model import UserGameStats
from app.models.user import User


class XPAwardResult(TypedDict):
    transaction: XPTransaction
    new_total_xp: int
    new_level: int
    leveled_up: bool
    xp_earned: int


class XPService:
    """Service for managing XP and leveling"""

    @staticmethod
    def award_xp(
        user_id,
        amount,
        transaction_type: XPTransactionTypeEnum,
        game_id=None,
        session_id=None,
        reference_id=None,
        meta: dict[str, Any] = {},
    ) -> tuple[Optional[XPAwardResult], Optional[str]]:
        """Award XP to a user"""

        user: User | None = User.query.get(user_id)
        if not user:
            return None, "User not found"

        transaction = XPTransaction(
            user_id=user_id,
            xp_amount=amount,
            type=transaction_type,
            game_id=game_id,
            session_id=session_id,
            reference_id=reference_id,
            meta=meta,
        )

        db.session.add(transaction)

        leveled_up = user.add_xp(amount)

        db.session.commit()

        return {
            "transaction": transaction,
            "new_total_xp": user.total_xp,
            "new_level": user.current_level,
            "leveled_up": leveled_up,
            "xp_earned": amount,
        }, None

    @staticmethod
    def process_session_completion(session_id) -> Optional[XPAwardResult]:
        """Process XP rewards for completed session"""

        session: GameSession | None = GameSession.query.get(session_id)
        if not session or not session.completed:
            return None

        game = session.game
        xp_calc = game.xp_calculation or {}

        base_xp = xp_calc.get("base", 10)

        score_multiplier = xp_calc.get("score_multiplier", 0)
        score_xp = int(session.score * score_multiplier) if score_multiplier else 0

        time_bonus = XPService._calculate_time_bonus(session, xp_calc)

        streak_bonus = XPService._calculate_streak_bonus(
            session.user_id, session.game_id, xp_calc
        )

        total_xp = base_xp + score_xp + time_bonus + streak_bonus

        # Award XP
        result, _ = XPService.award_xp(
            user_id=session.user_id,
            amount=total_xp,
            transaction_type=XPTransactionTypeEnum.GAME_COMPLETION,
            game_id=session.game_id,
            session_id=session_id,
            meta={
                "base_xp": base_xp,
                "score_xp": score_xp,
                "time_bonus": time_bonus,
                "streak_bonus": streak_bonus,
                "score": session.score,
            },
        )

        session.xp_earned = total_xp

        XPService.update_user_game_stats(session.user_id, session.game_id, session)

        db.session.commit()

        return result

    @staticmethod
    def _calculate_time_bonus(session: GameSession, xp_calc):
        """Calculate bonux XP based on completion time"""
        time_bonus_config = xp_calc.get("time_bonus", {})
        if not time_bonus_config:
            return 0

        target_time = time_bonus_config.get("target_seconds", 60)
        bonus_per_second = time_bonus_config.get("bonus_per_second", 0.5)
        max_bonus = time_bonus_config.get("max_bonus", 50)

        if session.duration_seconds < target_time:
            saved_seconds = target_time * session.duration_seconds
            bonus = int(saved_seconds * bonus_per_second)
            return min(bonus, max_bonus)

        return 0

    @staticmethod
    def _calculate_streak_bonus(user_id: uuid.UUID, game_id: uuid.UUID, xp_calc):
        """Calculate bonus XP based on play streak"""

        streak_bonus_config = xp_calc.get("streak_bonus", {})
        if not streak_bonus_config:
            return 0

        stats: UserGameStats | None = UserGameStats.query.filter_by(
            user_id=user_id,
            game_id=game_id,
        ).first()

        if not stats:
            return 0

        bonus_per_day = streak_bonus_config.get("bonus_per_day", 5)
        max_bonus = streak_bonus_config.get("max_bonus", 100)

        bonus = stats.current_streak * bonus_per_day
        return min(bonus, max_bonus)

    @staticmethod
    def update_user_game_stats(
        user_id: uuid.UUID,
        game_id: uuid.UUID,
        session: GameSession,
    ):
        """Update user's stats for a specific game"""
        stats: UserGameStats | None = UserGameStats.query.filter_by(
            user_id=user_id,
            game_id=game_id,
        ).first()

        if not stats:
            stats = UserGameStats(user_id=user_id, game_id=game_id)
            db.session.add(stats)

        stats.games_played += 1

        if session.completed:
            stats.games_completed += 1

        stats.total_xp_earned += session.xp_earned

        if stats.last_played_at:
            days_since = (datetime.now(timezone.utc) - stats.last_played_at).days
            if days_since == 1:
                stats.current_streak += 1
            elif days_since > 1:
                stats.current_streak = 1
        else:
            stats.current_streak = 1

        stats.best_streak = max(stats.best_streak, stats.current_streak)
        stats.last_played_at = datetime.now(timezone.utc)

        if session.final_stats:
            current_stats = stats.custom_stats or {}

            for key, value in session.final_stats.items():
                if isinstance(value, (int, float)):
                    current_stats[key] = current_stats.get(key, 0) + value
                else:
                    current_stats[key] = value

            stats.custom_stats = current_stats

        if session.score:
            if stats.best_score < session.score:
                stats.best_score = session.score

            if stats.average_score == 0:
                stats.average_score = session.score
            else:
                total_score = (
                    stats.average_score * (stats.games_completed - 1) + session.score
                )
                stats.average_score = total_score / stats.games_completed

        db.session.commit()
