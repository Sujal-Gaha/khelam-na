from flasgger import Swagger
from flask import Flask

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api-docs",
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Khelam Na API",
        "description": "API Documentation for Khelam Na Application",
        "contact": {
            "email": "suzalgahamagar@gmail.com",
        },
        "version": "1.0.0",
    },
    "basePath": "/api/v1",
    "schemes": ["http", "https"],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"',
        }
    },
}


def init_swagger(app: Flask):
    """Initialize Flasgger with the app"""
    return Swagger(app, config=swagger_config, template=swagger_template)
