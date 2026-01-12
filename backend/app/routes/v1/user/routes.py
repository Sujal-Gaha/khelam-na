from flask import Blueprint, Response, jsonify, request
from marshmallow import ValidationError

from app.extensions import db
from app.models.user import User
from app.schemas.user import (
    GetAllUsersInputSchema,
    GetAllUsersResponseSchema,
    GetUserByIdInputSchema,
    GetUserByIdResponseSchema,
    UserResponseSchema,
)

bp: Blueprint = Blueprint("users", __name__)

# Initialize schemas
user_response_schema = UserResponseSchema()
users_response_schema = UserResponseSchema(many=True)


@bp.route("/user/get_all_users", methods=["GET"])
def get_all_users() -> Response | tuple[Response, int]:
    """
    Get all users
    ---
    tags:
      - Users
    operationId: get_all_users
    summary: Retrieve all users
    description: Returns a list of all users in the system
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
        minimum: 1
        description: Page number
      - name: per_page
        in: query
        type: integer
        default: 10
        minimum: 1
        maximum: 100
        description: Number of users per page (max 100)
      - name: search
        in: query
        type: string
        description: Search users by name or email
      - name: sort_by
        in: query
        type: string
        enum: [name, email, created_at]
        default: created_at
        description: Field to sort by
      - name: order
        in: query
        type: string
        enum: [asc, desc]
        default: desc
        description: Sort order
    responses:
      "200":
        description: A list of users
        schema:
          type: object
          properties:
            data:
              type: object
              properties:
                data:
                  type: array
                  description: list of users
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                        example: 1
                      username:
                        type: string
                        example: johndoe
                      email:
                        type: string
                        example: john@example.com
                      created_at:
                        type: string
                        format: date-time
                        example: "2026-01-01T12:00:00"
                      updated_at:
                        type: string
                        format: date-time
                        example: "2026-01-01T12:00:00"
                pagination:
                  type: object
                  properties:
                    page:
                      type: integer
                      example: 1
                    per_page:
                      type: integer
                      example: 10
                    total:
                      type: integer
                      example: 100
                    pages:
                      type: integer
                      example: 10
                    has_next:
                      type: boolean
                      example: true
                    has_prev:
                      type: boolean
                      example: false
        "400":
          description: Bad request - Invalid parameters
          schema:
            type: object
            properties:
              error:
                type: string
                example: Invalid page or per_page parameter
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
        # Get pagination parameters
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        search = request.args.get("search", "", type=str)
        sort_by = request.args.get("sort_by", "created_at", type=str)
        order = request.args.get("order", "desc", type=str)

        input_schema = GetAllUsersInputSchema()
        errors = input_schema.validate({"page": page, "per_page": per_page})

        if errors:
            return jsonify({"error": errors}), 400

        if sort_by not in ["username", "email", "created_at"]:
            return (
                jsonify(
                    {
                        "error": "Invalid sort_by field. Must be one of: username, email, created_at"
                    }
                ),
                400,
            )

        if order not in ["asc", "desc"]:
            return jsonify({"error": "Order must be 'asc' or 'desc'"}), 400

        # Build query
        query = User.query.filter_by(is_deleted=False)

        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                )
            )

        # Apply sorting
        sort_column = getattr(User, sort_by)
        if order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        total = query.count()
        paginated_users = query.paginate(page=page, per_page=per_page, error_out=False)

        response = {
            "data": {
                "data": paginated_users.items,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "pages": paginated_users.pages,
                    "has_next": paginated_users.has_next,
                    "has_prev": paginated_users.has_prev,
                },
            }
        }

        serialized_data = GetAllUsersResponseSchema().dump(response)

        return jsonify(serialized_data), 200

    except ValidationError as e:
        return jsonify({"error": e.messages}), 400

    except Exception as e:
        return jsonify({"error": "An unexpected error occured", "details": str(e)}), 500


@bp.route("/user/get_user_by_id", methods=["GET"])
def get_user_by_id() -> Response | tuple[Response, int]:
    """
    Get user by Id
    ---
    tags:
      - Users
    operationId: get_user_by_id
    summary: Retrieve user by id
    description: Returns user by id in the system
    parameters:
      - name: user_id
        in: query
        type: integer
        description: The id of the user
    responses:
      "200":
        description: A user by id
        schema:
          type: object
          properties:
            user:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                name:
                  type: string
                  example: johndoe
                email:
                  type: string
                  example: john@example.com
                created_at:
                  type: string
                  format: date-time
                  example: "2026-01-09T12:00:00"
                updated_at:
                  type: string
                  format: date-time
                  example: "2026-01-09T12:00:00"
      "400":
        description: Bad request - Invalid parameters
        schema:
          type: object
          properties:
            error:
              type: string
              example: User id must be provided
      "404":
        description: Not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: User not found
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
        user_id = request.args.get("user_id", type=int)

        input_schema = GetUserByIdInputSchema()
        errors = input_schema.validate({"id": user_id})

        if errors:
            return jsonify({"error": errors}), 400

        if user_id is None:
            return jsonify({"error": "User id is required"}), 400

        user = User.query.filter_by(id=user_id, is_deleted=False).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        response = {"data": user}
        serialized_data = GetUserByIdResponseSchema().dump(response)

        return jsonify(serialized_data), 200

    except ValidationError as e:
        return jsonify({"error": e.messages}), 400

    except Exception as e:
        return jsonify({"error": "An unexpected error occured", "details": str(e)}), 500
