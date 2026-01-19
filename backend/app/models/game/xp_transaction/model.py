import uuid
import enum

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, UUID, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.user import User


class XPTransactionTypeEnum(enum.Enum):
    GAME_COMPLETION = "GAME_COMPLETION"
    ACHIEVEMENT = "ACHIEVEMENT"
    DAILY_BONUS = "DAILY_BONUS"
    STREAK_BONUS = "STREAK_BONUS"
    PENALTY = "PENALTY"


class XPTransaction(db.Model):
    """XP transaction model"""

    __tablename__ = "xp_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    game_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("games.id"), nullable=True
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("game_sessions.id"), nullable=True
    )

    xp_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[XPTransactionTypeEnum] = mapped_column(
        Enum(XPTransactionTypeEnum), nullable=False
    )

    reference_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped[User] = relationship("User", backref="xp_transactions")

    def __init__(
        self,
        user_id: uuid.UUID,
        xp_amount: int,
        type: XPTransactionTypeEnum,
        reference_id: Optional[str] = None,
        game_id: Optional[uuid.UUID] = None,
        session_id: Optional[uuid.UUID] = None,
        meta: dict[str, Any] = {},
    ):
        self.user_id = user_id
        self.xp_amount = xp_amount
        self.type = type
        self.reference_id = reference_id
        self.game_id = game_id if game_id else None
        self.session_id = session_id if session_id else None
        self.meta = meta

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "game_id": self.game_id,
            "session_id": self.session_id,
            "xp_amount": self.xp_amount,
            "type": self.type,
            "meta": self.meta,
            "created_at": self.created_at,
        }

    def __repr__(self):
        return f"<XPTransaction {self.xp_amount}xp for user {self.user_id}>"
