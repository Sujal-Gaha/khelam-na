from marshmallow import pre_load


class StripLowerMixin:
    @pre_load
    def clean_input(self, data, **kwargs):
        if "email" in data and isinstance(data["email"], str):
            data["email"] = data["email"].strip().lower()

        if "name" in data and isinstance(data["name"], str):
            data["name"] = data["name"].strip()

        print(f"StripLowerMixin kwargs: {kwargs}")

        return data
