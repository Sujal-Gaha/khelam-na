from flask import Flask
from flask_cors import CORS

from .config import Config
from .extensions import db, migrate


def create_app(config_class=Config) -> Flask:
    app: Flask = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app, origins=app.config["CORS_ORIGINS"])

    db.init_app(app)
    migrate.init_app(app, db)

    print(f"configuration is {app.config}")

    from .routes.v1 import bp as v1_bp

    app.register_blueprint(v1_bp, url_prefix="/api/v1")

    return app
