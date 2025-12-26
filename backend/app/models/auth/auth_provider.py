from app.extensions import db
from app.models.auth.enums import AuthProviderEnum
from datetime import datetime, timezone


class AuthProvider(db.Model):
    """OAuth/Social authentication providers linked to users"""

    __tablename__ = "auth_providers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )

    # Provider info
    provider = db.Column(db.Enum(AuthProviderEnum), nullable=False, index=True)
    provider_user_id = db.Column(
        db.String(255), nullable=False
    )  # User id from the provider

    # Additional provider data (store as JSON)
    provider_data = db.Column(db.JSON, nullable=True)  # email, name, avatar, etc.

    # Timestamps
    linked_at = db.Column(
        db.DateTime, nullable=False, default=datetime.now(timezone.utc)
    )
    last_used_at = db.Column(db.DateTime, nullable=True)

    # Unique constraint: one provider per user
    __table_args__ = (
        db.UniqueConstraint("user_id", "provider", name="uq_user_provider"),
        db.UniqueConstraint("provider", "provider_user_id", name="uq_provider_user_id"),
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
