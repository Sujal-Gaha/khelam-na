from flask import Flask

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402
from app.config import DevConfig  # noqa: E402

app: Flask = create_app(config_class=DevConfig)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4321)
