import uuid

from datetime import datetime, timezone
from typing import Optional

from app.extensions import db
from app.models.game import Game, GameSession, GameSessionStatusEnum
from app.models.user.model import User
from app.services.achievement_service import AchievementService
from app.services.leaderboard_service import LeaderboardService
from app.services.xp_service import XPService


class SessionService:
    """Service for managing game sessions"""

    @staticmethod
    def start_session(game_id, user_id, initial_state=None):
        """Start a new game session"""

        game: Game | None = Game.query.get(game_id)

        if not game or not game.is_active:
            return None, "Game not found or inactive"

        user: User | None = User.query.get(user_id)

        if not user:
            return None, "User not found"

        session = GameSession(
            game_id=game_id,
            user_id=user_id,
            game_state=initial_state or {},
            status=GameSessionStatusEnum.IN_PROGRESS,
        )

        db.session.add(session)

        game.play_count += 1

        db.session.commit()

        return session, None

    @staticmethod
    def update_session_state(session_id, new_state):
        """Update the game state of an active session"""

        session: GameSession | None = GameSession.query.get(session_id)
        if not session:
            return None, "Session is not active"

        session.game_state = new_state
        db.session.commit()

        return session, None

    @staticmethod
    def complete_session(session_id, final_score, final_stats=None):
        """
        Complete a game session and trigger XP/achievement processing

        Args:
            session_id: UUID of the session
            final_score: Final score achieved
            final_stats: Dict of game-specific stats
        """
        session: GameSession | None = GameSession.query.get(session_id)
        if not session:
            return None, "Session not found"

        if session.status != GameSessionStatusEnum.IN_PROGRESS:
            return None, "Session is not active"

        duration = (datetime.now(timezone.utc) - session.started_at).total_seconds()

        session.status = GameSessionStatusEnum.COMPLETED
        session.completed = True
        session.score = final_score
        session.final_stats = final_stats or {}
        session.duration_seconds = int(duration)
        session.completed_at = datetime.now(timezone.utc)

        db.session.commit()

        # Process XP and stats
        xp_result = XPService.process_session_completion(session_id=session_id)

        if not xp_result:
            return None, "XP result not found"

        unlocked_achievements = AchievementService.check_achievements(
            user_id=session.user_id, game_id=session.game_id
        )

        LeaderboardService.update_user_rakings(
            user_id=session.user_id, game_id=session.game_id
        )

        return {
            "session": session,
            "xp_earned": xp_result.get("xp_earned", 0),
            "new_level": xp_result.get("new_level"),
            "leveled_up": xp_result.get("leveled_up", False),
            "unlocked_achievements": unlocked_achievements,
        }, None

    @staticmethod
    def abandon_session(session_id: uuid.UUID):
        """Mark a session as abandoned"""
        session: GameSession | None = GameSession.query.get(session_id)
        if not session:
            return None, "Session not found"

        session.status = GameSessionStatusEnum.ABANDONED
        session.completed_at = datetime.now(timezone.utc)
        db.session.commit()

        return session, None

    @staticmethod
    def get_user_sessions(
        user_id: uuid.UUID,
        status: Optional[GameSessionStatusEnum],
        game_id: Optional[uuid.UUID] = None,
        limit=20,
    ):
        """Get sessions for a user"""

        query = GameSession.query.filter_by(user_id=user_id)

        if game_id:
            query = query.filter_by(game_id=game_id)

        if status:
            query = query.filter_by(status=status)

        return query.order_by(GameSession.started_at.desc()).limit(limit).all()

    @staticmethod
    def get_active_session(user_id: uuid.UUID, game_id: uuid.UUID):
        """Get the active session for auser in a specific game"""

        return GameSession.query.filter_by(
            user_id=user_id, game_id=game_id, status=GameSessionStatusEnum.IN_PROGRESS
        ).first()
