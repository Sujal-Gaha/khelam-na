from marshmallow import pre_load


class StripLowerMixin:
    """
    Mixin to strip whitespace and convert to lowercase for specified fields.
    Apply to schemas that need email/text normalization.
    """

    @pre_load
    def strip_and_lower(self, data, **kwargs):
        """
        Strip whitespace and convert to lowercase for string fields.
        Particularly useful for email and username fields.
        """
        if not isinstance(data, dict):
            return data

        # Fields that should be stripped and lowercased
        strip_lower_fields = ["email", "slug"]

        # Fields that should only be stripped (preserve case)
        strip_fields = ["username"]

        for field in strip_lower_fields:
            if field in data and isinstance(data[field], str):
                data[field] = data[field].strip().lower()

        for field in strip_fields:
            if field in data and isinstance(data[field], str):
                data[field] = data[field].strip()

        print(f"kwargs missed: {kwargs}")
        return data
