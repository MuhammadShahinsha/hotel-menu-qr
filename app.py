from flask import Flask, render_template, request, redirect, session, flash, jsonify
import sqlite3
import qrcode

app = Flask(__name__)
app.secret_key = "secret123"
DB_NAME = "database.db"

# ---------- DATABASE ----------
def get_db():
    return sqlite3.connect(DB_NAME)

def init_db():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER,
        category_id INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS variants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        menu_id INTEGER,
        variant_name TEXT,
        price INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        items TEXT,
        total INTEGER
    )
    """)

    # Categories
    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO categories (name) VALUES (?)",
            [
                ("Biryani",),
                ("Mandi",),
                ("Mojitos",),
                ("Juices",)
            ]
        )

    # Menu
    cur.execute("SELECT COUNT(*) FROM menu")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO menu (name, price, category_id) VALUES (?,?,?)",
            [
                # Biryani (price handled by variants)
                ("Chicken Biryani", None, 1),
                ("Mutton Biryani", None, 1),
                ("Beef Biryani", None, 1),
                ("Fish Biryani", None, 1),
                ("Prawn Biryani", None, 1),

                # Mandi
                ("Chicken Mandi", None, 2),
                ("Mutton Mandi", None, 2),
                ("Beef Mandi", None, 2),
                ("Honey Chicken Mandi", None, 2),
                ("Peri Peri Mandi", None, 2),
                ("Alfaham Mandi", None, 2),

                # Mojitos (normal items)
                ("Black Currant Mojito", 90, 3),
                ("Pineapple Mojito", 80, 3),
                ("Strawberry Mojito", 80, 3),
                ("Green Apple Mojito", 80, 3),
                ("Classic Mojito", 70, 3),

                # Juices
                ("Orange Juice", 50, 4),
                ("Mango Juice", 60, 4),
                ("Pineapple Juice", 50, 4),
                ("Lemonade", 30, 4),
                ("Watermelon Juice", 50, 4),
            ]
        )

    # Variants
    cur.execute("SELECT COUNT(*) FROM variants")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO variants (menu_id, variant_name, price) VALUES (?,?,?)",
            [
                # Chicken Biryani
                (1, "Full", 180),
                (1, "Half", 120),

                # Mutton Biryani
                (2, "Full", 260),
                (2, "Half", 180),

                # Beef Biryani
                (3, "Full", 220),
                (3, "Half", 150),

                # Fish Biryani
                (4, "Full", 240),
                (4, "Half", 170),

                # Prawn Biryani
                (5, "Full", 300),
                (5, "Half", 200),
            

                # Chicken Mandi
                (6, "Full", 280),
                (6, "Half", 200),
                (6, "Quarter", 150),

                # Mutton Mandi
                (7, "Full", 400),
                (7, "Half", 300),
                (7, "Quarter", 220),

                # Beef Mandi
                (8, "Full", 320),
                (8, "Half", 220),
                (8, "Quarter", 170),

                # Honey Chicken Mandi
                (9, "Full", 300),
                (9, "Half", 220),
                (9, "Quarter", 170),

                # Peri Peri Mandi
                (10, "Full", 300),
                (10, "Half", 220),
                (10, "Quarter", 170),

                # Alfaham Mandi
                (11, "Full", 350),
                (11, "Half", 250),
                (11, "Quarter", 200),
            ]
        )

    db.commit()
    db.close()

# ---------- ROUTES ----------
@app.route("/")
def index():
    qr = qrcode.make("http://127.0.0.1:5000/menu")
    qr.save("static/qr.png")
    return render_template("index.html")

@app.route("/menu")
def menu():
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT id, name FROM categories")
    categories = cur.fetchall()

    menu_data = {}

    for cat in categories:
        cur.execute(
            "SELECT id, name, price FROM menu WHERE category_id=?",
            (cat[0],)
        )
        items = cur.fetchall()

        item_list = []
        for item in items:
            cur.execute(
                "SELECT variant_name, price FROM variants WHERE menu_id=?",
                (item[0],)
            )
            variants = cur.fetchall()

            item_list.append({
                "name": item[1],
                "price": item[2],
                "variants": variants
            })

        menu_data[cat[1]] = item_list

    db.close()
    return render_template("menu.html", menu_data=menu_data)

# ---------- AJAX ADD TO CART ----------
@app.route("/add_to_cart_ajax", methods=["POST"])
def add_to_cart_ajax():
    data = request.get_json()
    name = data["item_name"]
    price = int(data["price"])

    if "cart" not in session:
        session["cart"] = []

    session["cart"].append({
        "name": name,
        "price": price
    })

    session.modified = True
    return jsonify({"message": f"✅ {name} added to cart"})

@app.route("/cart")
def cart():
    cart = session.get("cart", [])
    total = sum(i["price"] for i in cart)
    return render_template("cart.html", cart=cart, total=total)

@app.route("/remove_item/<int:index>")
def remove_item(index):
    cart = session.get("cart", [])
    if 0 <= index < len(cart):
        cart.pop(index)
        session.modified = True
    return redirect("/cart")

@app.route("/confirm_order")
def confirm_order():
    cart = session.get("cart", [])
    total = sum(i["price"] for i in cart)
    items = ", ".join(i["name"] for i in cart)

    db = get_db()
    cur = db.cursor()
    cur.execute("INSERT INTO orders (items, total) VALUES (?,?)", (items, total))
    db.commit()
    db.close()

    session.pop("cart", None)
    return render_template("success.html", total=total)

init_db()

if __name__ == "__main__":
    app.run()

