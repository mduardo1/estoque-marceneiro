import os
from pathlib import Path

from flask import Flask

BASE_DIR = Path(__file__).resolve().parent.parent


def load_env_file():
    env_path = BASE_DIR / ".env"

    try:
        from dotenv import load_dotenv
    except ImportError:
        load_dotenv = None

    if load_dotenv:
        load_dotenv(env_path, override=False)
        return

    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key:
            os.environ.setdefault(key, value)


load_env_file()

from app.database import create_tables
from app.routes.auth_routes import auth_bp
from app.routes.customer_routes import customer_bp
from app.routes.menu_routes import menu_bp
from app.routes.order_routes import order_bp
from app.routes.product_routes import product_bp


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "estoque_marceneiro_chave")

create_tables()

app.register_blueprint(auth_bp)
app.register_blueprint(menu_bp)
app.register_blueprint(product_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(order_bp)


if __name__ == "__main__":
    app.run(debug=True)
