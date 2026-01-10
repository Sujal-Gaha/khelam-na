import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""

    # App
    APP_NAME: str = os.getenv("APP_NAME", "Khelan Na")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_key")
    DEBUG: bool = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    # Database
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL", "sqlite:///instance/app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # CORS
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")

    # JWT Token Settings
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(days=30)

    # Security
    BCRYPT_LOG_ROUNDS: int = 12  # For password hashing
    SESSION_COOKIE_SECURE: bool = (
        os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
    )
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"

    OTP_LENGTH: int = 6
    OTP_EXPIRY_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 5

    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCK_MINUTES: int = 30

    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100


class ProdConfig(Config):
    """Production configuration"""

    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

    # Use environment variables for production
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")  # Must be set in production
    SQLALCHEMY_DATABASE_URI: str = os.getenv("DATABASE_URL", "")  # Must be set


class DevConfig(Config):
    """Development configuration"""

    DEBUG: bool = True
    TESTING: bool = False


class TestConfig(Config):
    """Testing configuration"""

    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    WTF_CSRF_ENABLED: bool = False


config_by_name = {
    "dev": DevConfig,
    "prod": ProdConfig,
    "test": TestConfig,
    "default": DevConfig,
}
