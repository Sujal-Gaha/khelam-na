from typing import List, cast
import qrcode
import io
import base64

from app.models.auth.auth_provider import AuthProvider
from app.models.auth.enums import AuthProviderEnum
from app.models.auth.refresh_token import RefreshToken
from app.models.user import User
from app.models.auth import OTPCode
from app.extensions import db


class AuthService:
    """Authentication service with OTP, 2FA, and OAuth support"""

    @staticmethod
    def send_login_otp(email):
        """Send OTP for passwordless login"""

        try:
            user = User.query.filter_by(email=email).first()

            if not user:
                return False, "No account found with this email"

            if user.is_deleted:
                return False, "Account no longer exists"

            if not user.is_active:
                return False, "Account is deactivated"

            if user.is_account_locked():
                return False, "Account is locked. Try again later."

            OTPCode.create_and_send(purpose="login", email=email, user_id=user.id)

            return True, None

        except Exception as e:
            return False, str(e)

    @staticmethod
    def verify_login_otp(email, code, ip_address=None):
        try:
            if not OTPCode.verify_code(code, "login", email=email):
                return None, None, None, "Invalid or expired OTP"

            user = User.query.filter_by(email=email).first()

            if not user:
                return None, None, None, "User not found"

            user.reset_failed_login(ip_address)

            access_token = user.generate_access_token()
            refresh_token = user.generate_refresh_token()

            return access_token, refresh_token, user, None

        except Exception as e:
            return None, None, None, str(e)

    @staticmethod
    def register_with_password(username, email, password):
        """Register user with password and send verification OTP"""
        try:
            if User.query.filter_by(email=email).first():
                return None, "User already exists"

            user = User(username=username, email=email, password=password)
            db.session.add(user)
            db.session.commit()
            db.session.refresh(user)

            OTPCode.create_and_send(
                purpose="email_verification", email=email, user_id=user.id
            )

            return user, None

        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def login_with_password(email, password, ip_address=None):
        """Login with email and password"""
        try:
            user = User.query.filter_by(email=email).first()

            if not user:
                return None, None, None, False, "Invalid credentials"

            if user.is_deleted:
                return None, None, None, False, "Account no longer exists"

            if not user.is_active:
                return None, None, None, False, "Account is deactivated"

            if user.is_account_locked():
                return None, None, None, False, "Account is locked"

            if not user.verify_password(password):
                user.increment_failed_login()
                return None, None, None, False, "Invalid credentials"

            # Check if 2FA is enabled

            if user.is_2fa_enabled:
                return None, None, user, True, None

            user.reset_failed_login(ip_address)

            access_token = user.generate_access_token()
            refresh_token = user.generate_refresh_token()

            return access_token, refresh_token, user, False, None

        except Exception as e:
            return None, None, None, False, str(e)

    @staticmethod
    def send_verification_otp(email):
        """Send email verification OTP"""
        try:
            user = User.query.filter_by(email=email).first()
            if not user:
                return False, "User not found"

            if user.is_email_verified:
                return False, "Email already verified"

            OTPCode.create_and_send(
                purpose="email_verification", email=email, user_id=user.id
            )

            return True, None

        except Exception as e:
            return False, str(e)

    @staticmethod
    def verify_email_otp(email, code):
        """Verify email using OTP"""
        try:
            if not OTPCode.verify_code(code, "email_verification", email=email):
                return False, "Invalid or expired OTP"

            user = User.query.filter_by(email=email).first()

            if user:
                user.is_email_verified = True
                db.session.commit()

            return True, None

        except Exception as e:
            return False, str(e)

    @staticmethod
    def send_password_reset_otp(email):
        """Send password reset OTP"""
        try:
            user = User.query.filter_by(email=email).first()

            if not user or user.is_deleted:
                return True, None

            OTPCode.create_and_send(
                purpose="password_reset", email=email, user_id=user.id
            )

            return True, None

        except Exception as e:
            return False, str(e)

    @staticmethod
    def reset_password_with_otp(email, code, new_password):
        """Reset password using OTP"""
        try:
            if not OTPCode.verify_code(code, "password_reset", email=email):
                return False, "Invalid or expired OTP"

            user = User.query.filter_by(email=email).first()

            if not user:
                return False, "User not found"

            user.set_password(new_password)
            user.failed_login_attempts = 0
            user.locked_until = None

            for token in user.refresh_tokens:
                token.revoke()

            db.session.commit()

            return True, None

        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def enable_2fa(user):
        """Enable 2FA for user"""
        try:
            totp_secret, backup_codes = user.enable_2fa()

            uri = user.get_totp_uri()
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(uri)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            buffer = io.BytesIO()
            img.save(buffer, kind="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()

            return img_str, backup_codes, None

        except Exception as e:
            return None, None, str(e)

    @staticmethod
    def verify_2fa_and_login(user: User, code, ip_address=None):
        """Verify 2FA code and complete login"""

        try:
            if user.verify_totp(code):
                user.reset_failed_login(ip_address)
                access_token = user.generate_access_token()
                refresh_token = user.generate_refresh_token()

                return access_token, refresh_token, None

            if user.verify_backup_code(code):
                user.reset_failed_login(ip_address)
                access_token = user.generate_access_token()
                refresh_token = user.generate_refresh_token()
                return access_token, refresh_token, None

            user.increment_failed_login()
            return None, None, "Invalid 2FA code"

        except Exception as e:
            return None, None, str(e)

    @staticmethod
    def refresh_access_token(refresh_token):
        """Generate new access token using refresh token"""
        try:
            user = RefreshToken.verify_and_get_user(refresh_token)

            if not user:
                return None, "Invalid or expired refresh token"

            if not user.is_active or user.is_deleted:
                return None, "User account is not active"

            access_token = user.generate_access_token()

            return access_token, None

        except Exception as e:
            return None, str(e)

    @staticmethod
    def logout(refresh_token):
        """Logout by revoking refresh token"""
        try:
            token = RefreshToken.query.filter_by(token=refresh_token).first()

            if token:
                token.revoke()
            return True, None

        except Exception as e:
            return False, str(e)

    @staticmethod
    def logout_all_devices(user: User):
        """Logout from all devices by revoking all refresh tokens"""
        try:
            for token in user.refresh_tokens:
                token.revoke()

            db.session.commit()

            return True, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    # ==================== OAUTH ====================
    @staticmethod
    def login_or_register_with_oauth(
        provider: AuthProviderEnum,
        provider_user_id,
        email,
        username,
        avatar_url=None,
        provider_data=None,
    ):
        """
        Login or register user via OAuth provider

        Args:
            provider: 'google', 'github', etc. (string or AuthProviderEnum)
            provider_user_id: Provider's user ID
            email: User's email
            name: User's name
            avatar_url: Profile picture URL
            provider_data: Additional data from provider (dict)

        Returns:
            tuple: (access_token, refresh_token, user, error)
        """
        try:
            # Convert string to enum
            if isinstance(provider, str):
                try:
                    provider = AuthProviderEnum(provider.lower())
                except ValueError:
                    return None, None, None, f"Unsupported provider: {provider}"

            # Find user by OAuth provider
            user = AuthProvider.find_by_provider(provider, provider_user_id)

            # If not found, check by email

            if not user and email:
                user = User.query.filter_by(email=email).first()

                # Link OAuth to existing user
                if user:
                    user.add_auth_provider(provider, provider_user_id, provider_data)

                    # Update user info if needed
                    if avatar_url and not user.avatar_url:
                        user.avatar_url = avatar_url

                    user.is_email_verified = True
                    db.session.commit()

            # Create new user if not found
            if not user:
                user = User(
                    username=username,
                    email=email,
                    is_email_verified=True,
                    avatar_url=avatar_url,
                )
                db.session.add(user)
                db.session.flush()  # Get user.id

                # Link OAuth provider
                user.add_auth_provider(provider, provider_user_id, provider_data)

                db.session.commit()

            # Generate tokens
            access_token = user.generate_access_token()
            refresh_token = user.generate_refresh_token()

            return access_token, refresh_token, user, None

        except Exception as e:
            db.session.rollback()
            return None, None, None, str(e)

    @staticmethod
    def link_oauth_provider(user, provider, provider_user_id, provider_data=None):
        """
        Link additional OAuth provider to existing user

        Args:
            user: User instance
            provider: Provider name (string or AuthProviderEnum)
            provider_user_id: Provider's user ID
            provider_data: Additional provider data

        Returns:
            tuple: (success, error)
        """
        try:
            if isinstance(provider, str):
                try:
                    provider = AuthProviderEnum(provider.lower())
                except ValueError:
                    return False, f"Unsupported provider: {provider}"

            # Check if provider already linked to another user
            existing = AuthProvider.find_by_provider(provider, provider_user_id)

            if existing and existing.id != user.id:
                return (
                    False,
                    f"{provider.value.title()} account already linked to another user",
                )

            user.add_auth_provider(provider, provider_user_id, provider_data)

            return True, None

        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def unlink_oauth_provider(user: User, provider):
        """
        Unlink OAuth provider from user

        Args:
            user: User instance
            provider: Provider name (string or AuthProviderEnum)

        Returns:
            tuple: (success, error)
        """
        try:
            if isinstance(provider, str):
                try:
                    provider = AuthProviderEnum(provider.lower())
                except ValueError:
                    return False, f"Unsupported provider: {provider}"

            # Check if user has password or other providers
            user_auth_providers = cast(List[AuthProvider], user.auth_providers)

            if not user.has_password() and len(user_auth_providers) <= 1:
                return (
                    False,
                    "Cannot unlink last authentication method. Please set a password first.",
                )

            if user.remove_auth_provider(provider):
                return True, None
            else:
                return False, f"{provider.value.title()} account not linked"

        except Exception as e:
            db.session.rollback()
            return False, str(e)
