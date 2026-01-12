from flask import Flask
from flask_cors import CORS

from app.swagger import init_swagger

from .config import Config
from .extensions import db, migrate

from .routes.v1.user import bp as user_bp_v1
from .routes.v1.auth import bp as auth_bp_v1


def create_app(config_class=Config) -> Flask:
    app: Flask = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app, origins=app.config["CORS_ORIGINS"])

    db.init_app(app)
    migrate.init_app(app, db)

    from .models.user import User
    from .models.auth import AuthProvider, AuthProviderEnum, OTPCode, RefreshToken 

    app.register_blueprint(user_bp_v1, url_prefix="/api/v1")
    app.register_blueprint(auth_bp_v1, url_prefix="/api/v1")

    init_swagger(app)

    return app
