import uuid

from sqlalchemy import UUID, DateTime, Float, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import  datetime, timezone
from app.extensions import db

from app.models.user import User
from app.models.game.leaderboard import Leaderboard
          

class LeaderboardEntry(db.Model):
    __tablename__ = 'leaderboard_entries'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    leaderboard_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('leaderboards.id'), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)

    rank: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    score_value: Mapped[float] = mapped_column(Float, nullable=False)
    games_played: Mapped[int] = mapped_column(Integer, default=0)

    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    leaderboard: Mapped[Leaderboard] = relationship('Leaderboard', back_populates='entries')
    user: Mapped[User] = relationship('User', backref='leaderboard_entries')

    __table_args__ = (
        Index('idx_leaderboard_rank', 'leaderboard_id', 'rank'),
        Index('idx_user_leaderboard', 'user_id', 'leaderboard_id'),
        UniqueConstraint('leaderboard_id', 'user_id', 'period_start', name="uq_leaderboard_user_period"),
    )

    def to_dict(self, include_user: bool = False):
        data = {
            'id': self.id,
            'leaderboard_id': self.leaderboard_id,
            'user_id': self.user_id,
            'rank': self.rank,
            'score_value': self.score_value,
            'games_played': self.games_played,
            'last_updated': self.last_updated,
        }

        if include_user and self.user:
            data['user'] = {
                'username': self.user.username,
                'avatar_url': self.user.avatar_url,
                'current_level': self.user.current_level,
            }

        return data

    def __repr__(self):
        return f"<LeaderboardEntry rank={self.rank} user={self.user_id}>"

