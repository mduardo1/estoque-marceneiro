import os
import sqlite3
import secrets
import smtplib
import ssl
import string
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import parseaddr

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


class EmailDeliveryError(RuntimeError):
    pass


def _generate_code(length=8):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _normalize_email(email):
    email = (email or "").strip().lower()
    return email or None


def _is_valid_email(email):
    if not email or any(char.isspace() for char in email):
        return False

    _, parsed_email = parseaddr(email)
    local_part, separator, domain = parsed_email.partition("@")
    return (
        parsed_email == email
        and bool(separator)
        and bool(local_part)
        and "." in domain
        and not domain.startswith(".")
        and not domain.endswith(".")
    )


def _smtp_port(value, fallback):
    raw_port = value or fallback or 587

    try:
        return int(raw_port)
    except (TypeError, ValueError) as error:
        raise EmailDeliveryError("Porta SMTP invalida. Verifique SMTP_PORT no arquivo .env.") from error


def _authentication_error_message(error, provider_name):
    smtp_code = getattr(error, "smtp_code", None)
    smtp_error = getattr(error, "smtp_error", b"")
    smtp_error_text = smtp_error.decode("utf-8", errors="ignore").lower() if isinstance(smtp_error, bytes) else str(smtp_error).lower()

    if provider_name == "gmail":
        if smtp_code == 534 or "application-specific password" in smtp_error_text or "app password" in smtp_error_text:
            return "Senha de aplicativo do Google invalida ou ausente. Gere uma senha de aplicativo e atualize SMTP_PASSWORD."

        if smtp_code == 535:
            return "Usuario SMTP ou senha de aplicativo incorretos. Verifique SMTP_USER e SMTP_PASSWORD."

        return "Autenticacao recusada pelo Gmail. Verifique se SMTP_USER e SMTP_PASSWORD usam uma senha de aplicativo."

    return "Usuario ou senha SMTP incorretos. Verifique SMTP_USER e SMTP_PASSWORD."


def _send_email(destination_email, subject, body):
    provider_name = os.getenv("EMAIL_PROVIDER", "custom").strip().lower()
    provider_config = SMTP_PROVIDERS.get(provider_name, SMTP_PROVIDERS["custom"])

    smtp_host = os.getenv("SMTP_HOST") or provider_config["host"]
    smtp_port = _smtp_port(os.getenv("SMTP_PORT"), provider_config["port"])
    smtp_user = (os.getenv("SMTP_USER") or "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD") or ""
    smtp_from = (os.getenv("SMTP_FROM") or smtp_user).strip()

    if not smtp_host or not smtp_user or not smtp_password or not smtp_from:
        raise EmailDeliveryError(
            "Envio de e-mail nao configurado. Defina "
            "SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD e SMTP_FROM."
        )

    if not _is_valid_email(destination_email):
        raise EmailDeliveryError("Endereco de e-mail do destinatario invalido.")

    if not _is_valid_email(smtp_from):
        raise EmailDeliveryError("Endereco de e-mail remetente invalido. Verifique SMTP_FROM.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = smtp_from
    message["To"] = destination_email
    message.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            server.login(smtp_user, smtp_password)
            server.send_message(message)
    except smtplib.SMTPAuthenticationError as error:
        raise EmailDeliveryError(_authentication_error_message(error, provider_name)) from error
    except smtplib.SMTPRecipientsRefused as error:
        raise EmailDeliveryError("Endereco de e-mail do destinatario recusado pelo servidor SMTP.") from error
    except smtplib.SMTPSenderRefused as error:
        raise EmailDeliveryError("Endereco de e-mail remetente recusado pelo servidor SMTP.") from error
    except smtplib.SMTPConnectError as error:
        raise EmailDeliveryError("Falha ao conectar ao servidor SMTP. Verifique host, porta e rede.") from error
    except TimeoutError as error:
        raise EmailDeliveryError("Tempo esgotado ao tentar enviar o e-mail. Verifique a conexao com a internet.") from error
    except OSError as error:
        raise EmailDeliveryError("Falha de conexao com o servidor SMTP. Verifique host, porta e rede.") from error
    except smtplib.SMTPException as error:
        raise EmailDeliveryError("Erro no envio SMTP. Verifique a configuracao do Gmail e tente novamente.") from error
    except Exception as error:
        raise EmailDeliveryError("Erro inesperado ao enviar o e-mail.") from error


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


def _is_expired(expires_at):
    return datetime.now(SAO_PAULO_TZ) > datetime.fromisoformat(expires_at)


def _log_verification_miss(cursor, email):
    latest = cursor.execute(
        """
        SELECT id, email, used, expires_at, created_at
        FROM account_verification_codes
        WHERE email = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (email,),
    ).fetchone()

    if latest:
        print(
            "[register/verify] Codigo nao encontrado para email normalizado. "
            f"email={email}, latest_id={latest['id']}, used={latest['used']}, "
            f"expires_at={latest['expires_at']}, created_at={latest['created_at']}"
        )
        return

    print(f"[register/verify] Codigo nao encontrado. Nenhum registro pendente para email={email}")


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

    if not _is_valid_email(email):
        return jsonify({"success": False, "message": "Informe um e-mail valido."}), 400

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

    pending_code = cursor.execute(
        """
        SELECT id, code, password, expires_at
        FROM account_verification_codes
        WHERE email = ? AND used = 0
        ORDER BY id DESC
        LIMIT 1
        """,
        (email,),
    ).fetchone()

    if pending_code and pending_code["password"] == password and not _is_expired(pending_code["expires_at"]):
        code = pending_code["code"]
        verification_id = pending_code["id"]
    else:
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
        if not pending_code or pending_code["id"] != verification_id:
            cursor.execute(
                "DELETE FROM account_verification_codes WHERE id = ?",
                (verification_id,),
            )
            conn.commit()
        conn.close()
        return jsonify({"success": False, "message": f"Nao foi possivel enviar o codigo: {error}"}), 500

    cursor.execute(
        """
        UPDATE account_verification_codes
        SET used = 1
        WHERE email = ? AND id <> ? AND used = 0
        """,
        (email, verification_id),
    )
    conn.commit()
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
        _log_verification_miss(cursor, email)
        conn.close()
        return jsonify({"success": False, "message": "Codigo invalido."}), 400

    if _is_expired(verification["expires_at"]):
        conn.close()
        return jsonify({"success": False, "message": "Codigo expirado."}), 400

    try:
        cursor.execute(
            """
            INSERT INTO users (username, password, email, phone, is_verified)
            VALUES (?, ?, ?, ?, 1)
            """,
            (email, verification["password"], email, None),
        )
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "message": "Ja existe uma conta com esse e-mail."}), 400

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

    if not _is_valid_email(email):
        return jsonify({"success": False, "message": "Informe um e-mail valido."}), 400

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
