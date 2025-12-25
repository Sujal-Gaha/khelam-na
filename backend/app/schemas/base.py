from marshmallow import Schema, EXCLUDE


class BaseSchema(Schema):
    """Base schema with common configuration"""

    class Meta:
        # Exclude unknown fields instead of raising an error
        unknown = EXCLUDE
        # Make datetime fields return UTC format
        datetimeformat = "utc"
        # Preserve field order
        ordered = True
