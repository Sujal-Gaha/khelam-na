from typing import Optional
from app.extensions import db
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, UniqueConstraint, Enum 
from sqlalchemy.orm import Mapped, mapped_column
import enum


class AuthProviderEnum(enum.Enum):
    """Enum for authentication providers"""

    GOOGLE = "google"
    GITHUB = "github"
    # Won't be adding more than this for now


class AuthProvider(db.Model):
    """OAuth/Social authentication providers linked to users"""

    __tablename__ = "auth_providers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    # Provider info
    provider: Mapped[AuthProviderEnum] = mapped_column(Enum(AuthProviderEnum), nullable=False, index=True)
    provider_user_id: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # User id from the provider

    # Additional provider data (store as JSON)
    provider_data: Mapped[dict] = mapped_column(JSON, nullable=True)  # email, name, avatar, etc.

    # Timestamps
    linked_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now(timezone.utc)
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Unique constraint: one provider per user
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_provider"),
        UniqueConstraint("provider", "provider_user_id", name="uq_provider_user_id"),
    )

    def __init__(self, user_id, provider, provider_user_id, provider_data):
        self.user_id = user_id
        self.provider = provider
        self.provider_user_id = provider_user_id
        self.provider_data = provider_data

    def updated_last_used(self):
        """Update last used timestamp"""
        self.last_used_at = datetime.now(timezone.utc)
        db.session.commit()

    def __repr__(self):
        return f"<AuthProvider {self.provider.value} for user {self.user_id}>"

    @staticmethod
    def find_by_provider(provider, provider_user_id):
        """
        Find user by OAuth provider

        Args:
            provider: AuthProviderEnum
            provider_user_id: User ID from provider

        Returns:
            User or None
        """
        if isinstance(provider, str):
            provider = AuthProviderEnum(provider)

            auth_provider = AuthProvider.query.filter_by(
                provider=provider,
                provider_user_id=provider_user_id,
            ).first()

            if auth_provider:
                auth_provider.updated_last_used()
                return auth_provider.user

            return None
