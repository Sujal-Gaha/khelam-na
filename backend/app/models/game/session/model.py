from datetime import datetime, timezone
import uuid
import enum

from sqlalchemy import JSON, UUID, Boolean, DateTime, Enum, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship
from app.extensions import db

class GameSessionStatusEnum(enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class GameSession(db.Model):
    __tablename__ = "game_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('games.id'), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)

    status: Mapped[GameSessionStatusEnum] = mapped_column(Enum(GameSessionStatusEnum), default=GameSessionStatusEnum.IN_PROGRESS, index=True)

    # Game state and results
    game_state: Mapped[dict] = mapped_column(JSON, default=dict)
    final_stats: Mapped[dict] = mapped_column(JSON, default=dict)

    score: Mapped[int] = mapped_column(Integer, default=0)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    game = relationship('Game', back_populates='sessions')
    user = relationship(
        'User', backref='game_sessions'
    )

    __table_args__ = (
        Index('idx_user_game_sessions', 'user_id', 'game_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'game_id': self.game_id,
            'user_id': self.user_id,
            'status': self.status,
            'score': self.score,
            'xp_earned': self.xp_earned,
            'completed': self.completed,
            'duration_seconds': self.duration_seconds,
            'started_at': self.started_at if self.started_at else None,
            'completed_at': self.completed_at if self.completed_at else None,
            'final_stats': self.final_stats
        }

    def __repr__(self):
        return f"<GameSession {self.id} - {self.status}>"

