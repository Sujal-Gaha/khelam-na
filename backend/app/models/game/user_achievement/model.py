from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import JSON, UUID, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.game.achievement.model import Achievement
from app.models.user.model import User


class UserAchievement(db.Model):
    __tablename__ = "user_achievements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    achievement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('achievements.id'), nullable=False)

    progress: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict) # Current progress toward achievement
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    # Relationships
    user: Mapped[User] = relationship('User', backref="achievements")
    achievement: Mapped[Achievement] = relationship('Achievement', back_populates='user_achievements')

    __table_args__ = (
        Index('idx_user_achievement', 'user_id', 'achievement_id'),
        UniqueConstraint('user_id', 'achievement_id', name='uq_user_achievement'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'achievement_id': self.achievement_id,
            'progress': self.progress,
            'unlocked_at': self.unlocked_at,
            'is_unlocked': self.unlocked_at is not None
        }

    def __repr__(self):
        return f"<UserAchievement user={self.user_id} achievement={self.achievement_id}>"
