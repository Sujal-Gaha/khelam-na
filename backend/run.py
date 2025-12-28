from flask import Flask

from app import create_app
from app.config import DevConfig

app: Flask = create_app(config_class=DevConfig)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4321)
