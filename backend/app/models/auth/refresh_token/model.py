from datetime import datetime, timezone
from app.extensions import db

from sqlalchemy import Integer, ForeignKey, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column


class RefreshToken(db.Model):
    """Store refresh tokens in database for revocation"""

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    token: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc)
    )

    # Track device/session info
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)

    def __init__(self, user_id, token, expires_at):
        self.user_id = user_id
        self.token = token
        self.expires_at = expires_at

    def is_valid(self):
        """Check if token is valid"""
        return not self.is_revoked and self.expires_at > datetime.now(timezone.utc)

    def revoke(self):
        """Revoke token"""
        self.is_revoked = True
        db.session.commit()

    @staticmethod
    def verify_and_get_user(token):
        """Verify refresh token and return user"""
        refresh_token = RefreshToken.query.filter_by(token=token).first()
        if refresh_token and refresh_token.is_valid():
            return refresh_token.user
        return None
