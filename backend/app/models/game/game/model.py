from datetime import datetime, timezone
import enum
import uuid

from typing import Any
from sqlalchemy import JSON, UUID, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db

class GameTypeEnum(enum.Enum):
    TURN_BASED="TURN_BASED"
    REAL_TIME = "REAL_TIME"
    SCORE_BASED = "SCORE_BASED"
    TIME_BASED = "TIME_BASED"
    TRIVIA = "TRIVIA"
    PUZZLE = "PUZZLE"


class GameScoringTypeEnum(enum.Enum):
    POINTS = "POINTS"
    TIME = "TIME"
    BOOLEAN = "BOOLEAN"
    PERCENTAGE = "PERCENTAGE"


class Game(db.Model):
    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[GameTypeEnum] = mapped_column(Enum(GameTypeEnum), nullable=False, index=True)

    # Flexible configuration
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    scoring_type: Mapped[GameScoringTypeEnum] = mapped_column(Enum(GameScoringTypeEnum), nullable=False, index=True)
    win_condition: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    xp_calculation: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    tracked_stats: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Game metadata
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('game_categories.id'))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    thumbnail_url: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    play_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship
    category = relationship('GameCategory', back_populates='games')
    sessions = relationship('GameSession', back_populates='game', lazy='dynamic', cascade='all, delete-orphan')
    user_stats = relationship('UserGameStats', back_populates='game', lazy='dynamic', cascade='all, delete-orphan')
    achievements = relationship('Achievement', back_populates='game', lazy='dynamic', cascade='all, delete-orphan')
    leaderboards = relationship('Leaderboard', back_populates='game', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_timestamps: bool = False, include_configs: bool = False):
        data = {
            'id': self.id,
            'slug': self.slug,
            'name': self.name,
            'type': self.type,
            'scoring_type': self.scoring_type,
            'category_id': self.category_id,
            'is_active': self.is_active,
            'thumbnail_url': self.thumbnail_url,
            'description': self.description,
            'play_count': self.play_count,
        }

        if include_timestamps:
            data['created_at'] = self.created_at
            data['updated_at'] = self.updated_at

        if include_configs:
            data['config'] = self.config,
            data['win_condition'] = self.win_condition
            data['xp_calculation'] = self.xp_calculation
            data['tracked_stats'] = self.tracked_stats

        return data

    
    def __repr__(self ):
        return f"<Game {self.name}>"
