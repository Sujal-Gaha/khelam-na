from flask import Blueprint, jsonify

bp = Blueprint("users", __name__)


@bp.route("/users", methods=["GET"])
def get_users():
    return jsonify({"users": []})
