from marshmallow import Schema, ValidationError, fields, validate, validates
from app.schemas.base import BaseSchema, SuccessSchema
from app.schemas.mixins import StripLowerMixin


class RegisterInputSchema(StripLowerMixin, BaseSchema):
    """Schema for user registration"""

    username = fields.Str(
        required=True,
        validate=validate.Length(min=8, max=100),
        error_messages={
            "required": "Username is required.",
            "invalid": "Username must be a string.",
        },
    )
    email = fields.Email(
        required=True,
        error_messages={
            "required": "Email is required.",
            "invalid": "Not a valid email address.",
        },
    )
    password = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(min=8),
        error_messages={
            "required": "Password id required.",
            "invalid": "Password must be a string.",
        },
    )

    @validates("username")
    def validate_username(self, value: str):
        """Additional validation for username"""
        if not value or not value.strip():
            raise ValidationError("Username cannot be empty or just whitespace.")

        if not any(c.isalpha() for c in value):
            raise ValidationError("Username must contain atleast one letter.")

    @validates("password")
    def validate_password(self, value: str):
        """Additional validation for password strength"""
        if not value or not value.strip():
            raise ValidationError("Password cannot be empty or just whitespace.")

        if len(value) < 8:
            raise ValidationError("Password must be at least 8 characters long.")


class LoginInputSchema(StripLowerMixin, BaseSchema):
    """Schema for user login"""

    email = fields.Email(
        required=True,
        error_messages={
            "required": "Email is required.",
            "invalid": "Not a valid email address.",
        },
    )
    password = fields.Str(
        required=True,
        load_only=True,
        error_messages={
            "required": "Password is required.",
            "invalid": "Password must be a string.",
        },
    )


class VerifyOTPInputSchema(StripLowerMixin, BaseSchema):
    """Schema for OTP verification"""

    email = fields.Email(
        required=True,
        error_messages={
            "required": "Email is required.",
            "invalid": "Not a valid email address.",
        },
    )
    code = fields.Str(
        required=True,
        validate=validate.Length(min=6, max=8),
        error_messages={
            "required": "2FA code is required.",
            "invalid": "Code must be a string",
        },
    )

    @validates("code")
    def validate_code(self, value: str):
        """Validate 2FA code format"""
        if not value or not value.strip():
            raise ValidationError("Code cannot be empty.")

        if not value.isdigit():
            raise ValidationError("Code must contain only digits.")


class SendOTPInputSchema(StripLowerMixin, BaseSchema):
    """Schema for sending OTP"""

    email = fields.Email(
        required=True,
        error_messages={
            "required": "Email is required.",
            "invalid": "Not a valid email address.",
        },
    )


class PasswordResetInputSchema(StripLowerMixin, BaseSchema):
    """Schema for password reset with OTP"""

    email = fields.Email(
        required=True,
        error_messages={
            "required": "Email is required",
            "invalid": "Not a valid email address.",
        },
    )
    code = fields.Str(
        required=True,
        validate=validate.Length(equal=6),
        error_messages={
            "required": "Verification code is required.",
            "invalid": "Code must be a string.",
        },
    )
    new_password = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(min=8),
        error_messages={
            "required": "New password is required.",
            "invalid": "Password must be a string.",
        },
    )

    @validates("code")
    def validate_code(self, value: str):
        """Validate OTP code format"""
        if not value or not value.strip():
            raise ValidationError("Code cannot be empty.")

        if not value.isdigit():
            raise ValidationError("Code must contain only digits.")

    @validates("new_password")
    def validate_new_password(self, value: str):
        """Validate password strength"""
        if not value or not value.strip():
            raise ValidationError("Password cannot be empty or just whitespace.")

        if len(value) < 8:
            raise ValidationError("Password must be at least 8 characters long.")


class Verify2FAInputSchema(BaseSchema):
    """Schema for 2FA verification"""

    user_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={
            "required": "User id is required.",
            "invalid": "User id must be a valid integer.",
        },
    )
    code = fields.Str(
        required=True,
        validate=validate.Length(min=6, max=8),
        error_messages={
            "required": "2FA code is required.",
            "invalid": "Code must be a string.",
        },
    )

    @validates("code")
    def validate_code(self, value: str):
        """Validate 2FA code format"""

        if not value or not value.strip():
            raise ValidationError("Code cannot be empty.")


class RefreshTokenInputSchema(BaseSchema):
    """Schema for refresh token"""

    refresh_token = fields.Str(
        required=True,
        error_messages={
            "required": "Refresh token is required.",
            "invalid": "Refresh token must be a string.",
        },
    )


class OAuthLoginInputSchema(BaseSchema):
    """Schema for OAuth login/registration"""

    provider_user_id = fields.Str(
        required=True,
        error_messages={
            "required": "Provider user id is required.",
            "invalid": "Provider user id must be a string.",
        },
    )
    email = fields.Email(
        required=True,
        error_messages={
            "required": "Email is required.",
            "invalid": "Not a valid email address.",
        },
    )
    username = fields.Str(
        required=True,
        validate=validate.Length(min=8, max=100),
        error_messages={
            "required": "Username is required.",
            "invalid": "Username must be a string.",
        },
    )
    avatar_url = fields.Str(
        required=False,
        validate=validate.URL(),
        error_messages={
            "invalid": "Avatar URL must be a valid URL.",
        },
    )
    provider_data = fields.Dict(
        required=False,
        error_messages={"invalid": "Provider data must be a valid dictionary."},
    )


class LinkOAuthProviderInputSchema(BaseSchema):
    """Schema for linking OAuth provider"""

    provider_user_id = fields.Str(
        required=True,
        error_messages={
            "required": "Provider user id is required.",
            "invalid": "Provider user id must be a string.",
        },
    )
    provider_data = fields.Dict(
        required=False,
        error_messages={
            "invalid": "Provider data must be a valid dictionary.",
        },
    )


class AuthTokenResponseSchema(SuccessSchema):
    """Schema for authentication token response"""

    data = fields.Nested(
        Schema.from_dict(
            {
                "access_token": fields.Str(),
                "refresh_token": fields.Str(),
                "user": fields.Dict(),
            }
        )
    )


class TwoFARequiredResponseSchema(SuccessSchema):
    """Schema for 2FA required response"""

    data = fields.Nested(
        Schema.from_dict(
            {
                "requires_2fa": fields.Bool(),
                "message": fields.Str(),
            }
        )
    )


class Enable2FAResponseSchema(SuccessSchema):
    """Schema for enable 2FA response"""

    data = fields.Nested(
        Schema.from_dict(
            {
                "qr_code": fields.Str(),
                "backup_codes": fields.List(fields.Str()),
                "message": fields.Str(),
            }
        )
    )
