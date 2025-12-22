import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev_key"
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")


class ProdConfig(Config):
    DEBUG = False


class DevConfig(Config):
    DEBUG = True
