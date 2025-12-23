import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_key")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    SQLALCHEMY_DATABASE_URI = os.environ["SQLALCHEMY_DATABASE_URI"]


class ProdConfig(Config):
    DEBUG = False


class DevConfig(Config):
    DEBUG = True
