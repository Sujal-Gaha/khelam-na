import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""

    # App
    APP_NAME = os.getenv("APP_NAME", "Khelan Na")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_key")
    DEBUG = os.getenv("FLASK_DEBUG", "False").lower()

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///instance/app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    # JWT Token Settings
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Security
    BCRYPT_LOG_ROUNDS = 12  # For password hashing
    SESSION_COOKIE_SECURE = (
        os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
    )
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 10
    OTP_MAX_ATTEMPTS = 5

    MAX_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCK_MINUTES = 30

    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100


class ProdConfig(Config):
    """Production configuration"""

    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

    # Use environment variables for production
    SECRET_KEY = os.getenv("SECRET_KEY")  # Must be set in production
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")  # Must be set


class DevConfig(Config):
    """Development configuration"""

    DEBUG = True
    TESTING = False


class TestConfig(Config):
    """Testing configuration"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config_by_name = {
    "dev": DevConfig,
    "prod": ProdConfig,
    "test": TestConfig,
    "default": DevConfig,
}
