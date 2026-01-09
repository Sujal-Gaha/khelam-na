from flask import Blueprint, Response, jsonify, request
from marshmallow import ValidationError

from app.schemas.auth_schema import RegisterInputSchema
from app.services.auth_service import AuthService


bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=["POST"])
def register() -> Response | tuple[Response, int]:
    """Register a new user with email and password"""
    try:
        schema = RegisterInputSchema()
        data = schema.load(request.get_json())

        user, error = AuthService.register_with_password(
            username=data["username"], email=data["email"], password=data["password"]
        )

        if error:
            return jsonify({"error": error}), 400

        return (
            jsonify(
                {
                    "message": "Registration successful. Please check your email for verification",
                    "user_id": user.id,
                }
            ),
            201,
        )

    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
