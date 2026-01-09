from marshmallow import Schema, ValidationError, fields, validate, validates
from .base import BaseSchema, SuccessSchema
from .mixins import StripLowerMixin


class UserResponseSchema(BaseSchema):
    """Schema for user responses"""

    id = fields.Int(dump_only=True)
    username = fields.Str()
    email = fields.Email()
    avatar_url = fields.Str(required=False)
    is_email_verified = fields.Bool()
    is_active = fields.Bool()
    is_deleted = fields.Bool()

    created_at = fields.DateTime(format="utc", dump_only=True)
    updated_at = fields.DateTime(format="utc", dump_only=True)


class CreateUserInputSchema(StripLowerMixin, BaseSchema):
    """Schema for creating user"""

    username = fields.Str(
        required=True,
        validate=validate.Length(min=8, max=100),
        error_messages={
            "required": "Name is required.",
            "invalid": "Name must be a string.",
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
            "required": "Password is required.",
            "invalid": "Password must be at least 8 characters long.",
        },
    )
    avatar_url = fields.Str(
        required=False,
    )

    @validates("username")
    def validate_name(self, value):
        """Additional validation for name"""
        if not value or not value.strip():
            raise ValidationError("Name cannot be empty or just whitespace.")

        # Check if name contains at least one letter
        if not any(c.isalpha() for c in value):
            raise ValidationError("Name must contain at least one letter.")


class CreateUserResponseSchema(SuccessSchema):
    """Schema for creating user response"""

    data = fields.Nested(UserResponseSchema, dump_only=True)


class GetAllUsersInputSchema(StripLowerMixin, BaseSchema):
    """Schema for getting all users"""

    page = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={
            "required": "Page is required.",
            "invalid": "Page must be a valid integer.",
        },
    )

    per_page = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={
            "required": "Per page is required.",
            "invalid": "Per page must be a valid integer.",
        },
    )


class GetAllUsersResponseSchema(SuccessSchema):
    """Schema for getting all users response"""

    data = fields.Nested(
        Schema.from_dict(
            {
                "data": fields.List(fields.Nested(UserResponseSchema)),
                "pagination": fields.Dict(),
            }
        )
    )


class GetUserByIdInputSchema(StripLowerMixin, BaseSchema):
    """Schema for getting user by id"""

    id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={
            "required": "Id is required.",
            "invalid": "Id must be a valid integer.",
        },
    )


class GetUserByIdResponseSchema(SuccessSchema):
    """Schema for getting user by id response"""

    data = fields.Nested(UserResponseSchema, dump_only=True)


class UpdateUserInputSchema(StripLowerMixin, BaseSchema):
    """Schema for updating user"""

    username = fields.Str(validate=validate.Length(min=8, max=100))
    avatar_url = fields.Str()

    @validates("username")
    def validate_username(self, value: str):
        """Validation for name"""
        if not value or not value.strip():
            raise ValidationError("Name cannot be empty or just whitespace.")
        if not any(c.isalpha() for c in value):
            raise ValidationError("Name must contain at least one letter.")


class UpdateUserResponseSchema(SuccessSchema):
    """Schema for updating user response"""

    data = fields.Nested(UserResponseSchema, dump_only=True)


class DeleteUserInputSchema(StripLowerMixin, BaseSchema):
    """Schema for deleting user"""

    id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={
            "required": "Id is required.",
            "invalid": "Id must be a valid integer.",
        },
    )
