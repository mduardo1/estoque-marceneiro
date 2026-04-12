from flask import Blueprint, request
from app.database import get_connection

product_bp = Blueprint("products", __name__)

@product_bp.route("/add_product", methods=["POST"])
def add_product():
    data = request.get_json()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO products (name, material, quantity, size) VALUES (?, ?, ?, ?)",
        (data["name"], data["material"], data["quantity"], data["size"])
    )

    conn.commit()
    conn.close()

    return {"message": "Produto adicionado com sucesso"}

@product_bp.route("/get_products", methods=["GET"])
def get_products():
    conn = get_connection()
    cursor = conn.cursor()

    products = cursor.execute("SELECT * FROM products").fetchall()

    conn.close()

    return [dict(p) for p in products]