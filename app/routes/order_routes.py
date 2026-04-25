from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from app.database import get_connection

order_bp = Blueprint("order", __name__)


@order_bp.route("/orders")
def orders():
    if "user_id" not in session:
        return redirect(url_for("auth.login_page"))
    return render_template("orders.html", email=session.get("user_email", ""))


@order_bp.route("/api/orders", methods=["GET"])
def list_orders():
    if "user_id" not in session:
        return jsonify({"message": "Usuario nao autenticado"}), 401

    conn = get_connection()
    cursor = conn.cursor()
    orders = cursor.execute(
        """
        SELECT
            orders.id,
            orders.customer_cnpj,
            orders.total_value,
            orders.created_at,
            GROUP_CONCAT(products.name, ', ') AS product_names
        FROM orders
        LEFT JOIN order_items ON order_items.order_id = orders.id
        LEFT JOIN products ON products.id = order_items.product_id
        WHERE orders.user_id = ?
        GROUP BY orders.id, orders.customer_cnpj, orders.total_value, orders.created_at
        ORDER BY orders.id DESC
        """,
        (session["user_id"],),
    ).fetchall()
    conn.close()

    return jsonify([dict(order) for order in orders])


@order_bp.route("/api/orders", methods=["POST"])
def create_order():
    if "user_id" not in session:
        return jsonify({"message": "Usuario nao autenticado"}), 401

    data = request.get_json() or {}
    customer_cnpj = (data.get("customer_cnpj") or "").strip()
    items = data.get("items") or []

    if not customer_cnpj:
        return jsonify({"message": "Informe o CNPJ do cliente."}), 400

    if not items:
        return jsonify({"message": "Adicione pelo menos um produto ao orcamento."}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    customer = cursor.execute(
        """
        SELECT id, trade_name
        FROM customers
        WHERE user_id = ? AND cnpj = ?
        """,
        (session["user_id"], customer_cnpj),
    ).fetchone()

    if not customer:
        conn.close()
        return jsonify({"message": "Cliente nao encontrado para o CNPJ informado."}), 404

    processed_items = []
    total_order_value = 0.0

    for index, item in enumerate(items, start=1):
        try:
            product_id = int(item.get("product_id"))
            quantity = int(item.get("quantity"))
        except (TypeError, ValueError):
            conn.close()
            return jsonify({"message": f"Linha {index}: ID e quantidade devem ser numericos."}), 400

        if quantity <= 0:
            conn.close()
            return jsonify({"message": f"Linha {index}: a quantidade deve ser maior que zero."}), 400

        product = cursor.execute(
            """
            SELECT id, name, quantity, price
            FROM products
            WHERE id = ? AND user_id = ?
            """,
            (product_id, session["user_id"]),
        ).fetchone()

        if not product:
            conn.close()
            return jsonify({"message": f"Linha {index}: produto nao encontrado."}), 404

        if product["quantity"] < quantity:
            conn.close()
            return jsonify(
                {
                    "message": (
                        f"Linha {index}: estoque insuficiente para o produto "
                        f"{product['name']}."
                    )
                }
            ), 400

        line_total = float(product["price"]) * quantity
        total_order_value += line_total
        processed_items.append(
            {
                "product_id": product["id"],
                "quantity": quantity,
                "unit_price": float(product["price"]),
                "total_price": line_total,
            }
        )

    cursor.execute(
        """
        INSERT INTO orders (user_id, customer_cnpj, total_value)
        VALUES (?, ?, ?)
        """,
        (session["user_id"], customer_cnpj, total_order_value),
    )
    order_id = cursor.lastrowid

    for item in processed_items:
        cursor.execute(
            """
            INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                order_id,
                item["product_id"],
                item["quantity"],
                item["unit_price"],
                item["total_price"],
            ),
        )
        cursor.execute(
            """
            UPDATE products
            SET quantity = quantity - ?
            WHERE id = ? AND user_id = ?
            """,
            (item["quantity"], item["product_id"], session["user_id"]),
        )

    conn.commit()
    conn.close()

    return (
        jsonify(
            {
                "message": f"Pedido salvo com sucesso para {customer['trade_name']}.",
                "order_id": order_id,
                "total_value": total_order_value,
            }
        ),
        201,
    )
