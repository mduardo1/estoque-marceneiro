from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from app.database import get_connection

customer_bp = Blueprint("customer", __name__)


@customer_bp.route("/customers")
def customers():
    if "user_id" not in session:
        return redirect(url_for("auth.login_page"))
    return render_template("customers.html", email=session.get("user_email", ""))


@customer_bp.route("/api/customers", methods=["GET"])
def list_customers():
    if "user_id" not in session:
        return jsonify({"message": "Usuario nao autenticado"}), 401

    conn = get_connection()
    cursor = conn.cursor()
    customers = cursor.execute(
        """
        SELECT id, trade_name, cnpj, phone, address
        FROM customers
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],),
    ).fetchall()
    conn.close()

    return jsonify([dict(customer) for customer in customers])


@customer_bp.route("/api/customers", methods=["POST"])
def create_customer():
    if "user_id" not in session:
        return jsonify({"message": "Usuario nao autenticado"}), 401

    data = request.get_json() or {}
    trade_name = (data.get("trade_name") or "").strip()
    cnpj = (data.get("cnpj") or "").strip()
    phone = (data.get("phone") or "").strip()
    address = (data.get("address") or "").strip()

    if not trade_name or not cnpj or not phone or not address:
        return jsonify({"message": "Preencha todos os campos do cliente."}), 400

    conn = get_connection()
    cursor = conn.cursor()

    existing_customer = cursor.execute(
        "SELECT id FROM customers WHERE user_id = ? AND cnpj = ?",
        (session["user_id"], cnpj),
    ).fetchone()

    if existing_customer:
        conn.close()
        return jsonify({"message": "Ja existe um cliente com esse CNPJ."}), 400

    cursor.execute(
        """
        INSERT INTO customers (user_id, trade_name, cnpj, phone, address)
        VALUES (?, ?, ?, ?, ?)
        """,
        (session["user_id"], trade_name, cnpj, phone, address),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Cliente salvo com sucesso."}), 201


@customer_bp.route("/api/customers/<int:customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    if "user_id" not in session:
        return jsonify({"message": "Usuario nao autenticado"}), 401

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM customers WHERE id = ? AND user_id = ?",
        (customer_id, session["user_id"]),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Cliente removido com sucesso."})
