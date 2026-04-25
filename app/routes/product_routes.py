from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from app.database import get_connection

product_bp = Blueprint("products", __name__)


def _parse_price(price_value):
    if price_value in [None, ""]:
        return 0.0

    normalized = str(price_value).strip().replace(".", "").replace(",", ".")
    return float(normalized)


@product_bp.route("/products", methods=["GET"])
def products_page():
    if "user_id" not in session:
        return redirect(url_for("auth.login_page"))

    return render_template("products.html", email=session.get("user_email", ""))


@product_bp.route("/add_product", methods=["POST"])
def add_product():
    if "user_id" not in session:
        return jsonify({"message": "Usuario nao autenticado"}), 401

    data = request.get_json() or {}

    name = data.get("name")
    material = data.get("material")
    quantity = data.get("quantity")
    size = data.get("size")
    price = data.get("price")

    if not name:
        return jsonify({"message": "Nome do produto e obrigatorio"}), 400

    try:
        parsed_quantity = int(quantity) if quantity not in [None, ""] else 0
        parsed_price = _parse_price(price)
    except ValueError:
        return jsonify({"message": "Quantidade e valor devem ser numericos"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO products (user_id, name, material, quantity, size, price)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                name,
                material,
                parsed_quantity,
                size,
                parsed_price,
            ),
        )

        conn.commit()
        conn.close()

        return jsonify({"message": "Produto adicionado com sucesso"}), 201

    except Exception as error:
        return jsonify({"message": f"Erro no servidor: {error}"}), 500


@product_bp.route("/get_products", methods=["GET"])
def get_products():
    if "user_id" not in session:
        return jsonify({"message": "Usuario nao autenticado"}), 401

    try:
        conn = get_connection()
        cursor = conn.cursor()

        products = cursor.execute(
            """
            SELECT id, name, material, quantity, size, price
            FROM products
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (session["user_id"],),
        ).fetchall()

        conn.close()

        return jsonify([dict(product) for product in products]), 200

    except Exception as error:
        return jsonify({"message": f"Erro ao buscar produtos: {error}"}), 500


@product_bp.route("/delete_product/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    if "user_id" not in session:
        return jsonify({"message": "Usuario nao autenticado"}), 401

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM products WHERE id = ? AND user_id = ?",
            (product_id, session["user_id"]),
        )

        conn.commit()
        conn.close()

        return jsonify({"message": "Produto removido com sucesso"}), 200

    except Exception as error:
        return jsonify({"message": f"Erro ao excluir produto: {error}"}), 500


@product_bp.route("/update_product_quantity/<int:product_id>", methods=["PUT"])
def update_product_quantity(product_id):
    if "user_id" not in session:
        return jsonify({"message": "Usuario nao autenticado"}), 401

    data = request.get_json() or {}

    try:
        quantity = int(data.get("quantity"))
    except (TypeError, ValueError):
        return jsonify({"message": "Informe uma quantidade valida."}), 400

    if quantity < 0:
        return jsonify({"message": "A quantidade nao pode ser negativa."}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE products
        SET quantity = ?
        WHERE id = ? AND user_id = ?
        """,
        (quantity, product_id, session["user_id"]),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Quantidade atualizada com sucesso."}), 200
