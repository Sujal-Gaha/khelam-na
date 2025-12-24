from flask import Blueprint, Response, jsonify

bp: Blueprint = Blueprint("users", __name__)


@bp.route("/user/get_all_users", methods=["GET"])
def get_all_users() -> Response:
    """
    Get all users
    ---
    tags:
      - Users
    operationId: get_all_users
    summary: Retrieve all users
    description: Returns a list of all users in the system
    responses:
      200:
        description: A list of users
        schema:
          type: object
          properties:
            users:
              type: array
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
    """
    return jsonify({"users": [{"name": "Ram"}]})
