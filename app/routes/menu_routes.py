from flask import Blueprint, redirect, render_template, session, url_for

from app.database import get_connection

menu_bp = Blueprint("menu", __name__)


def _require_login():
    if "user_id" not in session:
        return redirect(url_for("auth.login_page"))
    return None


@menu_bp.route("/menu")
def menu():
    redirect_response = _require_login()
    if redirect_response:
        return redirect_response

    return render_template("menu.html", email=session.get("user_email", ""))


@menu_bp.route("/dashboard")
def dashboard():
    redirect_response = _require_login()
    if redirect_response:
        return redirect_response

    conn = get_connection()
    cursor = conn.cursor()

    products_total = cursor.execute(
        "SELECT COUNT(*) AS total FROM products WHERE user_id = ?",
        (session["user_id"],),
    ).fetchone()["total"]

    low_stock_total = cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM products
        WHERE user_id = ? AND quantity <= 5
        """,
        (session["user_id"],),
    ).fetchone()["total"]

    customers_total = cursor.execute(
        "SELECT COUNT(*) AS total FROM customers WHERE user_id = ?",
        (session["user_id"],),
    ).fetchone()["total"]

    orders_total = cursor.execute(
        "SELECT COUNT(*) AS total FROM orders WHERE user_id = ?",
        (session["user_id"],),
    ).fetchone()["total"]

    conn.close()

    return render_template(
        "dashboard.html",
        email=session.get("user_email", ""),
        products_total=products_total,
        low_stock_total=low_stock_total,
        customers_total=customers_total,
        orders_total=orders_total,
    )
