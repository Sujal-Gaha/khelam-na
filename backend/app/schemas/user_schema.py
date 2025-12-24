from marshmallow import fields, validate
from .base import BaseSchema
from .mixins import StripLowerMixin


class UserCreateSchema(StripLowerMixin, BaseSchema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True)
    password = fields.Str(
        required=True, load_only=True, validate=validate.Length(min=8)
    )


class UserUpdateSchema(StripLowerMixin, BaseSchema):
    name = fields.Str(validate=validate.Length(min=2, max=100))
    email = fields.Email()
    password = fields.Str(load_only=True, validate=validate.Length(min=8))


class UserResponseSchema(BaseSchema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    email = fields.Email()
    created_at = fields.DateTime(format="iso", dump_only=True)
    updated_at = fields.DateTime(format="iso", dump_only=True)
