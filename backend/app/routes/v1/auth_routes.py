from typing import Any, cast
from flask import Blueprint, Response, jsonify, request
from marshmallow import ValidationError

from app.schemas.auth_schema import (
    LoginInputSchema,
    RegisterInputSchema,
    VerifyOTPInputSchema,
)
from app.services.auth_service import AuthService


bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=["POST"])
def register() -> Response | tuple[Response, int]:
    """Register a new user with email and password"""
    try:
        json_data = request.get_json()
        if not json_data:
            return jsonify({"error": "No data provided"}), 400

        schema = RegisterInputSchema()
        validated_data = schema.load(json_data)

        if not validated_data:
            return jsonify({"error": "Invalid data"}), 400

        data = cast(dict[str, Any], validated_data)

        user, error = AuthService.register_with_password(
            username=data["username"],
            email=data["email"],
            password=data.get("password"),
        )

        if error:
            return jsonify({"error": error}), 400

        if not user:
            return jsonify({"error": "Registration failed"}), 500

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


@bp.route("/login", methods=["POST"])
def login() -> Response | tuple[Response, int]:
    """Login with email and password"""
    try:
        json_data = request.get_json()
        if not json_data:
            return jsonify({"error": "No data provided"}), 400

        schema = LoginInputSchema()
        validated_data = schema.load(json_data)

        if not validated_data:
            return jsonify({"error": "Invalid data"}), 400

        data = cast(dict[str, Any], validated_data)

        ip_address = request.remote_addr

        access_token, refresh_token, user, error = AuthService.login_with_password(
            email=data["email"],
            password=data["password"],
            ip_address=ip_address,
        )

        if error:
            return jsonify({"error": error}), 401

        if not user:
            return jsonify({"error": "Login failed"}), 500

        return (
            jsonify(
                {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                    },
                }
            ),
            200,
        )

    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/send-verification-email", methods=["POST"])
def send_verification_email() -> Response | tuple[Response, int]:
    """Send email verification OTP"""
    try:
        json_data = request.get_json()
        if not json_data:
            return jsonify({"error": "No data provided"}), 400

        email = json_data.get("email")

        if not email:
            return jsonify({"error": "Email is required"}), 400

        success, error = AuthService.send_verification_otp(email)

        if error:
            return jsonify({"error": error}), 400

        return jsonify({"message": "OTP sent to your email"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/verify-email", methods=["POST"])
def verify_email() -> Response | tuple[Response, int]:
    """Verify email with OTP"""
    try:
        json_data = request.get_json()
        if not json_data:
            return jsonify({"error": "No data provided"}), 400

        schema = VerifyOTPInputSchema()
        validated_data = schema.load(json_data)

        if not validated_data:
            return jsonify({"error": "Invalid data"}), 400

        data = cast(dict[str, Any], validated_data)

        success, error = AuthService.verify_email_otp(
            email=data["email"], code=data["code"]
        )

        if error:
            return jsonify({"error": error}), 400

        return jsonify({"message": "Email verified successfully"}), 200

    except ValidationError as e:
        return jsonify({"error": e.messages}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/logout", methods=["POST"])
def logout() -> Response | tuple[Response, int]:
    """Logout current device"""
    try:
        json_data = request.get_json()
        if not json_data:
            return jsonify({"error": "No data provided"}), 400

        refresh_token = json_data.get("refresh_token")

        success, error = AuthService.logout(refresh_token)

        if error:
            return jsonify({"error": error}), 400

        return jsonify({"message": "Logged out successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
