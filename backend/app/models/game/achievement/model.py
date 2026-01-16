import uuid

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, UUID, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.game import Game, UserAchievement


class Achievement(db.Model):
    """Achievement model"""

    __tablename__ = "achievements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    game_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("games.id"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    icon_url: Mapped[str] = mapped_column(String(500))

    # Flexible requirement system
    requirement_definition: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    xp_reward: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    unlock_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc)
    )

    # Relationships
    game: Mapped[Game] = relationship("Game", back_populates="achievements")
    user_achievements: Mapped[list[UserAchievement]] = relationship(
        "UserAchievement",
        back_populates="achievement",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "game_id": self.game_id,
            "name": self.description,
            "description": self.description,
            "icon_url": self.icon_url,
            "xp_reward": self.xp_reward,
            "unlock_count": self.unlock_count,
            "requirement_definition": self.requirement_definition,
        }

    def __repr__(self):
        return f"<Achievement {self.name}>"
