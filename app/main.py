from flask import Flask, render_template
from app.database import create_tables
from app.routes.auth_routes import auth_bp
from app.routes.product_routes import product_bp

app = Flask(__name__)

create_tables()

app.register_blueprint(auth_bp)
app.register_blueprint(product_bp)

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/products")
def products():
    return render_template("products.html")

if __name__ == "__main__":
    app.run(debug=True)