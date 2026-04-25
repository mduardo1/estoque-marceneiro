import os
import secrets
import smtplib
import string
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from app.database import get_connection

auth_bp = Blueprint("auth", __name__)

SAO_PAULO_TZ = timezone(timedelta(hours=-3))

SMTP_PROVIDERS = {
    "gmail": {"host": "smtp.gmail.com", "port": 587},
    "outlook": {"host": "smtp.office365.com", "port": 587},
    "hotmail": {"host": "smtp.office365.com", "port": 587},
    "yahoo": {"host": "smtp.mail.yahoo.com", "port": 587},
    "icloud": {"host": "smtp.mail.me.com", "port": 587},
    "hostinger": {"host": "smtp.hostinger.com", "port": 587},
    "uol": {"host": "smtps.uol.com.br", "port": 587},
    "bol": {"host": "smtps.uol.com.br", "port": 587},
    "custom": {"host": None, "port": None},
}


def _generate_code(length=8):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _normalize_email(email):
    email = (email or "").strip().lower()
    return email or None


def _send_email(destination_email, subject, body):
    provider_name = os.getenv("EMAIL_PROVIDER", "custom").strip().lower()
    provider_config = SMTP_PROVIDERS.get(provider_name, SMTP_PROVIDERS["custom"])

    smtp_host = os.getenv("SMTP_HOST") or provider_config["host"]
    smtp_port = int(os.getenv("SMTP_PORT") or provider_config["port"] or 587)
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_user or "")

    if not smtp_host or not smtp_user or not smtp_password or not smtp_from:
        raise RuntimeError(
            "Envio de e-mail nao configurado. Defina EMAIL_PROVIDER e/ou "
            "SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD e SMTP_FROM."
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = smtp_from
    message["To"] = destination_email
    message.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(message)

def _send_code(destination_email, code, purpose):
    _send_email(
        destination_email,
        f"{purpose} - Estoque Marceneiro",
        (
            f"Codigo de verificacao: {code}\n"
            "Validade: 15 minutos.\n\n"
            "Se nao foi voce, ignore esta mensagem."
        ),
    )


def _current_expiration():
    return (datetime.now(SAO_PAULO_TZ) + timedelta(minutes=15)).isoformat()


def _find_user_by_field(cursor, field_name, value):
    if not value:
        return None

    return cursor.execute(
        f"SELECT id FROM users WHERE {field_name} = ? LIMIT 1",
        (value,),
    ).fetchone()


@auth_bp.route("/", methods=["GET"])
def login_page():
    if "user_id" in session:
        return redirect(url_for("menu.menu"))
    return render_template("login.html")


@auth_bp.route("/forgot-password-page", methods=["GET"])
def forgot_password_page():
    if "user_id" in session:
        return redirect(url_for("menu.menu"))
    return render_template("forgot_password.html")


@auth_bp.route("/register_page", methods=["GET"])
def register_page():
    if "user_id" in session:
        return redirect(url_for("menu.menu"))
    return render_template("register.html")


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    email = _normalize_email(data.get("email"))
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"success": False, "message": "Informe o e-mail e a senha."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    user = cursor.execute(
        """
        SELECT *
        FROM users
        WHERE (email = ? OR username = ?)
          AND password = ?
          AND is_verified = 1
        """,
        (email, email, password),
    ).fetchone()

    conn.close()

    if user:
        session["user_id"] = user["id"]
        session["user_email"] = user["email"] or user["username"] or ""
        return jsonify({"success": True, "message": "Login realizado com sucesso"})

    return jsonify({"success": False, "message": "E-mail, senha ou validacao da conta invalidos."}), 401


@auth_bp.route("/register/send-code", methods=["POST"])
def send_register_code():
    data = request.get_json() or {}

    email = _normalize_email(data.get("email"))
    password = data.get("password") or ""
    confirm_password = data.get("confirm_password") or ""

    if not email:
        return jsonify({"success": False, "message": "Informe o e-mail."}), 400

    if password != confirm_password:
        return jsonify({"success": False, "message": "As senhas nao conferem."}), 400

    if len(password) < 4:
        return jsonify({"success": False, "message": "A senha deve ter pelo menos 4 caracteres."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    existing_email = _find_user_by_field(cursor, "email", email)

    if existing_email:
        conn.close()
        return jsonify({"success": False, "message": "Ja existe uma conta com esse e-mail."}), 400

    cursor.execute(
        """
        DELETE FROM account_verification_codes
        WHERE email = ?
        """,
        (email,),
    )

    code = _generate_code()
    cursor.execute(
        """
        INSERT INTO account_verification_codes (email, phone, password, code, expires_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (email, None, password, code, _current_expiration()),
    )
    verification_id = cursor.lastrowid
    conn.commit()

    try:
        _send_code(email, code, "Criacao de conta")
    except Exception as error:
        cursor.execute(
            "DELETE FROM account_verification_codes WHERE id = ?",
            (verification_id,),
        )
        conn.commit()
        conn.close()
        return jsonify({"success": False, "message": f"Nao foi possivel enviar o codigo: {error}"}), 500

    conn.close()
    return jsonify({"success": True, "message": "Codigo enviado com sucesso."})


@auth_bp.route("/register/verify", methods=["POST"])
def verify_register_code():
    data = request.get_json() or {}

    email = _normalize_email(data.get("email"))
    code = (data.get("code") or "").strip().upper()

    if not code or not email:
        return jsonify({"success": False, "message": "Informe o codigo e o e-mail."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    verification = cursor.execute(
        """
        SELECT *
        FROM account_verification_codes
        WHERE email = ? AND code = ? AND used = 0
        ORDER BY id DESC
        LIMIT 1
        """,
        (email, code),
    ).fetchone()

    if not verification:
        conn.close()
        return jsonify({"success": False, "message": "Codigo invalido."}), 400

    if datetime.now(SAO_PAULO_TZ) > datetime.fromisoformat(verification["expires_at"]):
        conn.close()
        return jsonify({"success": False, "message": "Codigo expirado."}), 400

    cursor.execute(
        """
        INSERT INTO users (username, password, email, phone, is_verified)
        VALUES (?, ?, ?, ?, 1)
        """,
        (email, verification["password"], email, None),
    )
    cursor.execute(
        "UPDATE account_verification_codes SET used = 1 WHERE id = ?",
        (verification["id"],),
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Conta criada com sucesso. Agora voce ja pode entrar."})


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    email = _normalize_email(data.get("email"))

    if not email:
        return jsonify({"success": False, "message": "Informe o e-mail cadastrado."}), 400

    conn = get_connection()
    cursor = conn.cursor()
    user = cursor.execute("SELECT id, email FROM users WHERE email = ?", (email,)).fetchone()

    if not user:
        conn.close()
        return jsonify({"success": False, "message": "E-mail nao encontrado."}), 404

    code = _generate_code()
    cursor.execute(
        """
        INSERT INTO password_reset_codes (user_id, code, expires_at)
        VALUES (?, ?, ?)
        """,
        (user["id"], code, _current_expiration()),
    )
    reset_code_id = cursor.lastrowid
    conn.commit()

    try:
        _send_email(
            user["email"],
            "Recuperacao de senha - Estoque Marceneiro",
            (
                "Voce solicitou a recuperacao de senha.\n\n"
                f"Codigo de verificacao: {code}\n"
                "Validade: 15 minutos.\n\n"
                "Se nao foi voce, ignore este e-mail."
            ),
        )
    except Exception as error:
        cursor.execute("DELETE FROM password_reset_codes WHERE id = ?", (reset_code_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": False, "message": f"Nao foi possivel enviar o e-mail: {error}"}), 500

    conn.close()
    return jsonify({"success": True, "message": "Codigo enviado para o e-mail cadastrado."})


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json() or {}

    email = _normalize_email(data.get("email"))
    code = (data.get("code") or "").strip().upper()
    new_password = data.get("new_password") or ""
    confirm_password = data.get("confirm_password") or ""

    if not email or not code or not new_password or not confirm_password:
        return jsonify({"success": False, "message": "Preencha todos os campos."}), 400

    if new_password != confirm_password:
        return jsonify({"success": False, "message": "As senhas nao conferem."}), 400

    conn = get_connection()
    cursor = conn.cursor()
    user = cursor.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()

    if not user:
        conn.close()
        return jsonify({"success": False, "message": "E-mail nao encontrado."}), 404

    reset_code = cursor.execute(
        """
        SELECT id, expires_at
        FROM password_reset_codes
        WHERE user_id = ? AND code = ? AND used = 0
        ORDER BY id DESC
        LIMIT 1
        """,
        (user["id"], code),
    ).fetchone()

    if not reset_code:
        conn.close()
        return jsonify({"success": False, "message": "Codigo invalido."}), 400

    if datetime.now(SAO_PAULO_TZ) > datetime.fromisoformat(reset_code["expires_at"]):
        conn.close()
        return jsonify({"success": False, "message": "Codigo expirado."}), 400

    cursor.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, user["id"]))
    cursor.execute("UPDATE password_reset_codes SET used = 1 WHERE id = ?", (reset_code["id"],))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Senha redefinida com sucesso."})


@auth_bp.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logout realizado com sucesso"})
