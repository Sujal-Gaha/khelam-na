from marshmallow import Schema, EXCLUDE, fields


class BaseSchema(Schema):
    """Base schema with common configuration"""

    class Meta:
        # Exclude unknown fields instead of raising an error
        unknown = EXCLUDE
        # Make datetime fields return UTC format
        datetimeformat = "utc"
        # Preserve field order
        ordered = True


class SuccessSchema(Schema):
    message = fields.Str(required=True)
    is_success = fields.Bool(required=True, dump_default=True)


class ErrorSchema(Schema):
    error = fields.Str(required=True)
    is_success = fields.Bool(required=True, dump_default=False)
