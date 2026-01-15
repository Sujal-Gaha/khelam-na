import uuid

from datetime import datetime, timezone
from sqlalchemy import UUID, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db


class GameCategory(db.model):
    "Game category model"
    __tablename__ = "game_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default = uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    icon_url: Mapped[str] = mapped_column(String(500))
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    games = relationship('Game', back_populates='category', lazy='dynamic')

    def to_dict(self, include_timestamps: bool):
        game_category =  {
            'id': self.id,
            'name': self.name,
            'icon_url': self.icon_url,
            'display_order': self.display_order
        }

        if include_timestamps:
            game_category["created_at"]= self.created_at
            game_category["updated_at"] = self.updated_at

        return game_category

    def __repr__(self):
        return f"<GameCategory {self.name}>"

