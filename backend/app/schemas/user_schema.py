from marshmallow import ValidationError, fields, validate, validates
from .base import BaseSchema
from .mixins import StripLowerMixin


class UserCreateSchema(StripLowerMixin, BaseSchema):
    """Schema for creating a new user"""

    name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=100),
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
            "required": "Password id required",
            "invalid": "Password must be at least 8 characters long.",
        },
    )

    @validates("name")
    def validate_name(self, value):
        """Additional validation for name"""
        if not value or not value.strip():
            raise ValidationError("Name cannot be empty or just whitespace.")

        # Check if name contains at least one letter
        if not any(c.isalpha() for c in value):
            raise ValidationError("Name must contain at least one letter.")


class UserUpdateSchema(StripLowerMixin, BaseSchema):
    """Schema for updating an existing user"""

    name = fields.Str(
        validate=validate.Length(min=2, max=100),
        error_messages={"invalid": "Name must be between 2 and 100 characters."},
    )
    email = fields.Email(error_messages={"invalid": "Not a valid email address."})
    password = fields.Str(
        load_only=True,
        validate=validate.Length(min=8),
        error_messages={"invalid": "Password must bt at least 8 characters long."},
    )

    @validates("name")
    def validate_name(self, value):
        """Additional validation for name"""
        if value is not None:
            if not value.strip():
                raise ValidationError("Name cannot be empty or just whitespace.")

            if not any(c.isalpha() for c in value):
                raise ValidationError("Name must contain at least one letter.")


class UserResponseSchema(BaseSchema):
    """Schema for user responses"""

    id = fields.Int(dump_only=True)
    name = fields.Str()
    email = fields.Email()
    created_at = fields.DateTime(format="iso", dump_only=True)
    updated_at = fields.DateTime(format="iso", dump_only=True)


class UserListResponseSchema(BaseSchema):
    """Schema for user list responses"""

    users = fields.List(fields.Nested(UserResponseSchema))
    pagination = fields.Dict()
