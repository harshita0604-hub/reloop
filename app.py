from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

DATABASE = "database.db"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


# ==========================================
# INITIALIZE DATABASE
# ==========================================

def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            category TEXT NOT NULL,

            original_price REAL NOT NULL,

            offer_price REAL NOT NULL,

            quantity INTEGER NOT NULL,

            claimed_quantity INTEGER DEFAULT 0,

            condition TEXT,

            description TEXT,

            status TEXT DEFAULT 'Available'

        )
    """)

    conn.commit()

    conn.close()
    init_db()
@app.before_request
def ensure_database():
    init_db()
# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    return render_template("index.html")


# ==========================================
# BUSINESS DASHBOARD
# ==========================================

@app.route("/business")
def business():

    return render_template("business.html")


# ==========================================
# ADD PRODUCT
# ==========================================

@app.route("/add-product", methods=["POST"])
def add_product():

    name = request.form["name"]

    category = request.form["category"]

    original_price = float(
        request.form["original_price"]
    )

    offer_price = float(
        request.form["offer_price"]
    )

    quantity = int(
        request.form["quantity"]
    )

    condition = request.form["condition"]

    description = request.form.get(
        "description",
        ""
    )


    conn = get_db()

    conn.execute("""
        INSERT INTO products
        (
            name,
            category,
            original_price,
            offer_price,
            quantity,
            claimed_quantity,
            condition,
            description
        )

        VALUES (?, ?, ?, ?, ?, 0, ?, ?)

    """, (
        name,
        category,
        original_price,
        offer_price,
        quantity,
        condition,
        description
    ))


    conn.commit()

    conn.close()


    return redirect("/marketplace")


# ==========================================
# MARKETPLACE
# ==========================================

@app.route("/marketplace")
def marketplace():

    conn = get_db()

    products = conn.execute("""
        SELECT *
        FROM products

        WHERE status = 'Available'

        AND quantity > 0

        ORDER BY id DESC

    """).fetchall()


    conn.close()


    return render_template(
        "marketplace.html",
        products=products
    )


# ==========================================
# CLAIM PRODUCT
# ================from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)

# Always keep database in the project folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# INITIALIZE DATABASE
# ==========================================

def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            original_price REAL NOT NULL,
            offer_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            claimed_quantity INTEGER DEFAULT 0,
            condition TEXT,
            description TEXT,
            status TEXT DEFAULT 'Available'
        )
    """)

    conn.commit()
    conn.close()


# IMPORTANT:
# Initialize database when Gunicorn/Render starts
init_db()


# Also make sure the database exists before every request
@app.before_request
def ensure_database():
    init_db()


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# BUSINESS DASHBOARD
# ==========================================

@app.route("/business")
def business():
    return render_template("business.html")


# ==========================================
# ADD PRODUCT
# ==========================================

@app.route("/add-product", methods=["POST"])
def add_product():

    name = request.form["name"]
    category = request.form["category"]

    original_price = float(
        request.form["original_price"]
    )

    offer_price = float(
        request.form["offer_price"]
    )

    quantity = int(
        request.form["quantity"]
    )

    condition = request.form["condition"]

    description = request.form.get(
        "description",
        ""
    )

    conn = get_db()

    conn.execute("""
        INSERT INTO products (
            name,
            category,
            original_price,
            offer_price,
            quantity,
            claimed_quantity,
            condition,
            description
        )

        VALUES (?, ?, ?, ?, ?, 0, ?, ?)
    """, (
        name,
        category,
        original_price,
        offer_price,
        quantity,
        condition,
        description
    ))

    conn.commit()
    conn.close()

    return redirect("/marketplace")


# ==========================================
# MARKETPLACE
# ==========================================

@app.route("/marketplace")
def marketplace():

    conn = get_db()

    products = conn.execute("""
        SELECT *
        FROM products
        WHERE status = 'Available'
        AND quantity > 0
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "marketplace.html",
        products=products
    )


# ==========================================
# CLAIM PRODUCT
# ==========================================

@app.route("/claim/<int:product_id>")
def claim(product_id):

    conn = get_db()

    product = conn.execute("""
        SELECT *
        FROM products
        WHERE id = ?
    """, (product_id,)).fetchone()

    if product:

        new_quantity = product["quantity"] - 1

        new_claimed_quantity = (
            product["claimed_quantity"] + 1
        )

        if new_quantity <= 0:

            conn.execute("""
                UPDATE products
                SET
                    quantity = 0,
                    claimed_quantity = ?,
                    status = 'Claimed'
                WHERE id = ?
            """, (
                new_claimed_quantity,
                product_id
            ))

        else:

            conn.execute("""
                UPDATE products
                SET
                    quantity = ?,
                    claimed_quantity = ?
                WHERE id = ?
            """, (
                new_quantity,
                new_claimed_quantity
            ))

        conn.commit()

    conn.close()

    return redirect("/marketplace")


# ==========================================
# IMPACT DASHBOARD
# ==========================================

@app.route("/impact")
def impact():

    conn = get_db()

    total_products = conn.execute("""
        SELECT COUNT(*)
        FROM products
    """).fetchone()[0]

    available_quantity = conn.execute("""
        SELECT COALESCE(SUM(quantity), 0)
        FROM products
    """).fetchone()[0]

    total_claimed = conn.execute("""
        SELECT COALESCE(SUM(claimed_quantity), 0)
        FROM products
    """).fetchone()[0]

    total_savings = conn.execute("""
        SELECT COALESCE(
            SUM(
                (original_price - offer_price)
                * claimed_quantity
            ),
            0
        )
        FROM products
    """).fetchone()[0]

    rescued_value = conn.execute("""
        SELECT COALESCE(
            SUM(
                offer_price * claimed_quantity
            ),
            0
        )
        FROM products
    """).fetchone()[0]

    conn.close()

    return render_template(
        "impact.html",
        total_products=total_products,
        available_quantity=available_quantity,
        total_claimed=total_claimed,
        total_savings=total_savings,
        rescued_value=rescued_value
    )


# ==========================================
# START APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)
