from typing import Any, cast

from flask import Blueprint, Response, jsonify, request
from marshmallow import ValidationError

from app.schemas.auth import (
    LoginInputSchema,
    RegisterInputSchema,
    VerifyOTPInputSchema,
)
from app.services.auth_service import AuthService


bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=["POST"])
def register() -> Response | tuple[Response, int]:
    """
    Register new user
    ---
    tags:
      - Auth
    operationId: register
    summary: Register a new user
    description: Registers a new user in the system
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - email
            - password
          properties:
            username:
              type: string
              example: johndoe123
            email:
              type: string
              example: john@example.com
            password:
              type: string
              example: strongpassword123
    responses:
      "201":
        description: User registered
        schema:
          type: object
          properties:
            message:
              type: string
              example: Registration successful
            user_id:
              type: integer
              example: 1
      "400":
        description: Bad request - Invalid parameters
        schema:
          type: object
          properties:
            error:
              type: string
              example: Invalid email parameter
      "500":
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: An unexpected error occured

    """
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
    """
    Login user
    ---
    tags:
      - Auth
    operationId: login
    summary: Login user
    description: Login the user into the system
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: jhon@example.com
            password:
              type: string
              example: strongpassword123
    responses:
      "200":
        description: User logged in
        schema:
          type: object
          properties:
            access_token:
              type: string
              example: ksjdok....kkjdaf
            refresh_token:
              type: string
              example: klljl....sdfakl
            user:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                username:
                  type: string
                  example: johndoe123
                email:
                  type: string
                  example: john@example.com
      "400":
        description: Bad request - Invalid parameters
        schema:
          type: object
          properties:
            error:
              type: string
              example: Invalid data
      "401":
        description: Unauthorized
        schema:
          type: object
          properties:
            error:
              type: string
              example: Login failed. User unauthorized
      "500":
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: An unexpected error occured
    """
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
    """
    Send verification email to user
    ---
    tags:
      - Auth
    operationId: send-verification-email
    summary: Send verification email
    description: Send otp code to verify users email
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
          properties:
            email:
              type: string
              example: john@example.com
    responses:
      "200":
        descripion: Verification email sent
        schema:
          type: object
          properties:
            message:
              type: string
              example: OTP sent to your email
      "400":
        description: Bad request - Invalid parameter
        schema:
          type: object
          properties:
            error:
              type: string
              example: Email is required
      "500":
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: An unexpected error occured
    """
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
    """
    Verify email of user
    ---
    tags:
      - Auth
    operationId: verify-email
    summary: Send verification email
    description: Verify email of user
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
            - code
          properties:
            email:
              type: string
              example: john@example.com
            code:
              type: string
              example: 87654321
    responses:
      "200":
        description: Email verified
        schema:
          type: object
          properties:
            message:
              type: string
              example: Email verified successfully
      "400":
        description: Bad request - Invalid parameter
        schema:
          type: object
          properties:
            error:
              type: string
              example: Email is required
      "500":
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: An unexpected error occured
    """
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
    """
    Logout user
    ---
    tags:
      - Auth
    operationId: logout
    summary: Logout user
    description: Log out the user from the system
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - refresh_token
          properties:
            refresh_token:
              type: string
              example: jdlsk....akswl
    responses:
      "200":
        description: User logged out
        schema:
          type: object
          properties:
            message:
              type: string
              example: Logged out successfully
      "400":
        description: Bad request - Invalid parameter
        schema:
          type: object
          properties:
            error:
              type: string
              example: No data provided
      "500":
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: An unexpected error occured
    """
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
