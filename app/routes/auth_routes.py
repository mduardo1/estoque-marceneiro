from flask import Blueprint, request
from app.database import get_connection

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    conn = get_connection()
    cursor = conn.cursor()

    user = cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, password)
    ).fetchone()

    conn.close()

    if user:
        return {"success": True, "message": "Login realizado com sucesso"}, 200
    else:
        return {"success": False, "message": "Usuário ou senha inválidos"}, 401