import jwt
import pyotp
import secrets

from flask import current_app
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.auth.auth_provider import AuthProvider
from app.models.auth.enums import AuthProviderEnum
from app.models.auth.refresh_token import RefreshToken
from app.models.auth.otp_code import OTPCode


class User(db.Model):
    """User model"""

    __tablename__ = "users"

    # Basic Info
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        db.String(120), unique=True, nullable=False, index=True
    )
    phone: Mapped[str | None] = mapped_column(
        db.String(20), unique=True, nullable=True, index=True
    )
    password_hash: Mapped[str | None] = mapped_column(
        db.String(255), nullable=True
    )  # Nullable for OAuth-only users
    avatar_url = mapped_column(db.String(500), nullable=True)

    # Account Status
    is_email_verified: Mapped[bool] = mapped_column(
        db.Boolean, default=False, nullable=False
    )
    is_phone_verified: Mapped[bool] = mapped_column(
        db.Boolean, default=False, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False)

    # 2FA / TOTP
    totp_secret: Mapped[str | None] = mapped_column(db.String(32), nullable=True)
    is_2fa_enabled: Mapped[bool] = mapped_column(
        db.Boolean, default=False, nullable=False
    )
    backup_codes = mapped_column(db.Text, nullable=True)  # JSON string of backup codes

    # Security Tracking
    failed_login_attempts: Mapped[int] = mapped_column(
        db.Integer, default=0, nullable=False
    )
    locked_until = mapped_column(db.DateTime, nullable=True)
    last_login = mapped_column(db.DateTime, nullable=True)
    last_login_ip: Mapped[str | None] = mapped_column(db.String(45), nullable=True)

    # Timestamps
    created_at = mapped_column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = mapped_column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    auth_providers: Mapped[list["AuthProvider"]] = relationship(
        "AuthProvider", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    otp_codes: Mapped[list["OTPCode"]] = relationship(
        "OTPCode", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def __init__(self, name, email, password=None, **kwargs):
        self.name = name
        self.email = email

        if password:
            self.set_password(password)

        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def has_password(self) -> bool:
        return self.password_hash is not None and self.verify_password("") is False

    def set_password(self, password):
        """Has and set password"""
        self.password_hash = generate_password_hash(
            password, method="pbkdf2:sha256", salt_length=16
        )

    def verify_password(self, password):
        """Verify password"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    # OAuth Provider Methods
    def get_auth_provider(self, provider):
        """
        Get OAuth provider for this user

        Args:
            provider: AuthProviderEnum

        Returns:
            AuthProvider or None
        """
        if isinstance(provider, str):
            provider = AuthProviderEnum(provider)

        return AuthProvider.query.filter_by(user_id=self.id, provider=provider).first()

    def add_auth_provider(self, provider, provider_user_id, provider_data=None):
        """
        Link OAuth provider to user

        Args:
            provider: AuthProviderEnum
            provider_user_id: User ID from the provider
            provider_data: Additional data from provider (dict)

        Returns:
            AuthProvider instance
        """
        if isinstance(provider, str):
            provider = AuthProviderEnum(provider)

        # Check if already exists
        existing = self.get_auth_provider(provider)

        if existing:
            existing.provider_user_id = provider_user_id
            existing.provider_data = provider_data
            db.session.commit()
            return existing

        # Create new
        auth_provider = AuthProvider(
            user_id=self.id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_data=provider_data,
        )
        db.session.add(auth_provider)
        db.session.commit()
        return auth_provider

    def remove_auth_provider(self, provider):
        """Remove OAuth provider"""
        if isinstance(provider, str):
            provider = AuthProviderEnum(provider)

        auth_provider = self.get_auth_provider(provider)
        if auth_provider:
            db.session.delete(auth_provider)
            db.session.commit()
            return True
        return False

    def has_auth_provider(self, provider):
        """Check if user has linked OAuth provider"""
        return self.get_auth_provider(provider) is not None

    def get_linked_providers(self):
        """Get list of linked OAuth providers"""
        return [ap.provider.value for ap in self.auth_providers]

    # Account Security
    def is_account_locked(self):
        """Check if account is locked"""
        if self.locked_until and self.locked_until > datetime.now(timezone.utc):
            return True
        return False

    def increment_failed_login(self):
        """Increment failed login attempts"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        db.session.commit()

    def reset_failed_login(self, ip_address=None):
        """Reset failed login attempts"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login = datetime.now(timezone.utc)

        if ip_address:
            self.last_login_ip = ip_address
        db.session.commit()

    # JWT Token Methods
    def generate_access_token(self, expires_in=900):
        """Generate short-lived access token (15 minutes)"""
        payload = {
            "user_id": self.id,
            "email": self.email,
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    def generate_refresh_token(self):
        """Generate long-lived refresh token and store in DB"""
        token_string = secrets.token_urlsafe(32)
        refresh_token = RefreshToken(
            user_id=self.id,
            token=token_string,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db.session.add(refresh_token)
        db.session.commit()
        return token_string

    @staticmethod
    def verify_access_token(token):
        """Verify JWT access token"""
        try:
            payload = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )
            if payload.get("type") != "access":
                return None
            user = User.query.get(payload["user_id"])
            if user and user.is_active and not user.is_deleted:
                return user
            return None
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

    # 2FA / TOTP Methods
    def enable_2fa(self):
        """Enable 2FA and generate TOTP secret"""
        self.totp_secret = pyotp.random_base32()
        self.is_2fa_enabled = True

        # Generate backup codes
        backup_codes = [secrets.token_hex(4) for _ in range(10)]
        import json

        self.backup_codes = json.dumps(backup_codes)

        db.session.commit()

        return self.totp_secret, backup_codes

    def disable_2fa(self):
        """Disable 2FA"""
        self.totp_secret = None
        self.is_2fa_enabled = False
        self.backup_codes = None
        db.session.commit()

    def get_totp_uri(self):
        """Get TOTP URI for QR code generation"""
        if not self.totp_secret:
            return None
        return pyotp.totp.TOTP(self.totp_secret).provisioning_uri(
            name=self.email, issuer_name=current_app.config.get("APP_NAME", "KhelamNa")
        )

    def verify_totp(self, code):
        """Verify TOTP code"""
        if not self.totp_secret:
            return False
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(code, valid_window=1)

    def verify_backup_code(self, code):
        """Verify and consume backup code"""
        if not self.backup_codes:
            return False

        import json

        codes = json.loads(self.backup_codes)

        if code in codes:
            codes.remove(code)
            self.backup_codes = json.dumps(codes)
            db.session.commit()
            return True
        return False

    def __repr__(self):
        return f"<User {self.name}>"

    def to_dict(self, include_timestamps=False):
        """Convert user to dictionary"""
        user = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "avatar_url": self.avatar_url,
        }

        if include_timestamps:
            user["created_at"] = self.created_at.isoformat()
            user["updated_at"] = self.updated_at.isoformat()

        return user
