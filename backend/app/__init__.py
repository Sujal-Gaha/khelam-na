from flask import Flask
from flask_cors import CORS

from .config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app, origins=app.config["CORS_ORIGINS"])

    from .routes.v1 import bp as v1_bp

    app.register_blueprint(v1_bp, url_prefix="/api/v1")

    return app
