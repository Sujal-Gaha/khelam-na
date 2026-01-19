import enum
import uuid

from typing import Any, Optional
from app.extensions import db
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, JSON, ForeignKey, UniqueConstraint, Enum, UUID
from sqlalchemy.orm import Mapped, mapped_column


class AuthProviderEnum(enum.Enum):
    """Enum for authentication providers"""

    GOOGLE = "GOOGLE"
    GITHUB = "GITHUB"
    # Won't be adding more than this for now


class AuthProvider(db.Model):
    """OAuth/Social authentication providers linked to users"""

    __tablename__ = "auth_providers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Provider info
    provider: Mapped[AuthProviderEnum] = mapped_column(
        Enum(AuthProviderEnum), nullable=False, index=True
    )
    provider_user_id: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # User id from the provider
    provider_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )  # email, name, avatar, etc.

    # Timestamps
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Unique constraint: one provider per user
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_provider"),
        UniqueConstraint("provider", "provider_user_id", name="uq_provider_user_id"),
    )

    def __init__(
        self,
        user_id: uuid.UUID,
        provider: AuthProviderEnum,
        provider_user_id: str,
        provider_data: Optional[dict[str, Any]] = None,
    ):
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
    def find_by_provider(provider: AuthProviderEnum, provider_user_id: str):
        """
        Find user by OAuth provider

        Args:
            provider: AuthProviderEnum
            provider_user_id: User ID from provider

        Returns:
            User or None
        """
        if isinstance(provider, AuthProviderEnum):
            provider = AuthProviderEnum(provider)

            auth_provider = AuthProvider.query.filter_by(
                provider=provider,
                provider_user_id=provider_user_id,
            ).first()

            if auth_provider:
                auth_provider.updated_last_used()
                return auth_provider.user

            return None
