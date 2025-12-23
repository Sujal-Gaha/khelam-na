from flask import Blueprint, Response, jsonify

bp: Blueprint = Blueprint("users", __name__)


@bp.route("/users", methods=["GET"])
def get_users() -> Response:
    return jsonify({"users": []})
