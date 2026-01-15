import uuid

from sqlalchemy import (
    JSON,
    UUID,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone

from app.extensions import db
from app.models.user import User
from app.models.game import Game


class UserGameStats(db.Model):
    __tablename__ = "user_game_stats"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("games.id"), nullable=False, index=True
    )

    # Universal stats
    games_played: Mapped[int] = mapped_column(Integer, default=0)
    games_completed: Mapped[int] = mapped_column(Integer, default=0)
    total_xp_earned: Mapped[int] = mapped_column(Integer, default=0)

    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)

    # Game-specific stats (flexible)
    custom_stats: Mapped[dict] = mapped_column(JSON, default=dict)

    # Performance metrics
    average_score: Mapped[float] = mapped_column(Float, default=0.00)
    best_score: Mapped[float] = mapped_column(Float, default=0.00)

    last_played_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped[User] = relationship("User", backref="game_stats")
    game: Mapped[Game] = relationship("Game", back_populates="user_stats")

    __table_args__ = UniqueConstraint("user_id", "game_id", name="uq_user_game_stats")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "game_id": self.game_id,
            "games_played": self.games_played,
            "games_completed": self.games_completed,
            "total_xp_earned": self.total_xp_earned,
            "current_streak": self.current_streak,
            "best_streak": self.best_streak,
            "custom_stats": self.custom_stats,
            "average_score": self.average_score,
            "best_score": self.best_score,
            "last_played_at": self.last_played_at if self.last_played_at else None,
        }

    def __repr__(self):
        return f"<UserGameStats user={self.user_id} game={self.game_id}>"
