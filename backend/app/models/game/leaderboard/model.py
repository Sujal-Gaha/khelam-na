import uuid
import enum

from typing import Any, Optional
from sqlalchemy import JSON, UUID, Boolean, DateTime, Enum, ForeignKey, String
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.game import Game, LeaderboardEntry


class LeaderboardTimePeriodEnum(enum.Enum):
    ALL_TIME = "ALL_TIME"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


class Leaderboard(db.Model):
    __tablename__ = "leaderboards"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    game_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("games.id"), nullable=True
    )

    leaderboard_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ranking_criteria: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    time_period: Mapped[LeaderboardTimePeriodEnum] = mapped_column(
        Enum(LeaderboardTimePeriodEnum), default=LeaderboardTimePeriodEnum.ALL_TIME
    )
    reset_schedule: Mapped[str] = mapped_column(
        String(100)
    )  # Cron expression for periodic resets

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_reset_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    game: Mapped[Game] = relationship("Game", back_populates="leaderboards")
    entries: Mapped[list[LeaderboardEntry]] = relationship(
        "LeaderboardEntry",
        back_populates="leaderboard",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "game_id": self.game_id,
            "leaderboard_name": self.leaderboard_name,
            "ranking_criteria": self.ranking_criteria,
            "time_period": self.time_period,
            "is_active": self.is_active,
            "last_reset_at": self.last_reset_at if self.last_reset_at else None,
        }

    def __repr__(self):
        return f"<Leaderboard {self.leaderboard_name}>"
