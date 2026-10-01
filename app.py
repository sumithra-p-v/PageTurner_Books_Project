from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "pageturner-secret-key"

DATABASE = "books.db"


def get_db():
    # Open the SQLite database.
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_cart_count():
    # Add all quantities in the session cart.
    cart = session.get("cart", {})
    return sum(cart.values())


def get_cart_books():
    # Get the books currently stored in the cart.
    cart = session.get("cart", {})
    if not cart:
        return [], 0

    ids = [int(book_id) for book_id in cart.keys()]
    placeholders = ",".join(["?"] * len(ids))

    conn = get_db()
    books = conn.execute(
        f"SELECT * FROM books WHERE id IN ({placeholders})", ids
    ).fetchall()
    conn.close()

    items = []
    total = 0

    for book in books:
        quantity = cart.get(str(book["id"]), 0)
        item_total = book["price"] * quantity
        total += item_total
        items.append({
            "book": book,
            "quantity": quantity,
            "item_total": item_total
        })

    return items, total


@app.context_processor
def common_data():
    return {"cart_count": get_cart_count()}


@app.route("/")
def home():
    category = request.args.get("category", "")

    conn = get_db()

    if category:
        books = conn.execute(
            "SELECT * FROM books WHERE category = ? ORDER BY title",
            (category,)
        ).fetchall()
    else:
        books = conn.execute(
            "SELECT * FROM books ORDER BY id"
        ).fetchall()

    categories = conn.execute(
        "SELECT DISTINCT category FROM books ORDER BY category"
    ).fetchall()

    conn.close()

    return render_template(
        "home.html",
        books=books,
        categories=categories,
        selected_category=category
    )


@app.route("/book/<int:book_id>")
def book(book_id):
    conn = get_db()
    book_data = conn.execute(
        "SELECT * FROM books WHERE id = ?",
        (book_id,)
    ).fetchone()
    conn.close()

    if book_data is None:
        flash("Book not found.", "error")
        return redirect(url_for("home"))

    return render_template("book.html", book=book_data)


@app.route("/cart/add/<int:book_id>", methods=["POST"])
def add_to_cart(book_id):
    conn = get_db()
    book_data = conn.execute(
        "SELECT * FROM books WHERE id = ?",
        (book_id,)
    ).fetchone()
    conn.close()

    if book_data is None:
        flash("Book not found.", "error")
        return redirect(url_for("home"))

    if book_data["stock"] <= 0:
        flash("This book is out of stock.", "error")
        return redirect(url_for("book", book_id=book_id))

    cart = session.get("cart", {})
    key = str(book_id)
    current_quantity = cart.get(key, 0)

    if current_quantity >= book_data["stock"]:
        flash("You cannot add more than the available stock.", "error")
    else:
        cart[key] = current_quantity + 1
        session["cart"] = cart
        flash("Book added to cart!", "success")

    return redirect(request.referrer or url_for("home"))


@app.route("/cart")
def cart():
    items, total = get_cart_books()
    return render_template("cart.html", items=items, total=total)


@app.route("/cart/update/<int:book_id>", methods=["POST"])
def update_cart(book_id):
    try:
        quantity = int(request.form.get("quantity", 1))
    except ValueError:
        quantity = 1

    conn = get_db()
    book_data = conn.execute(
        "SELECT * FROM books WHERE id = ?",
        (book_id,)
    ).fetchone()
    conn.close()

    cart = session.get("cart", {})
    key = str(book_id)

    if book_data is None:
        cart.pop(key, None)
    elif quantity <= 0:
        cart.pop(key, None)
    elif quantity > book_data["stock"]:
        cart[key] = book_data["stock"]
        flash("Quantity changed to available stock.", "error")
    else:
        cart[key] = quantity

    session["cart"] = cart
    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:book_id>", methods=["POST"])
def remove_from_cart(book_id):
    cart = session.get("cart", {})
    cart.pop(str(book_id), None)
    session["cart"] = cart
    flash("Book removed from cart.", "success")
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, total = get_cart_books()

    if not items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        name = request.form.get("customer_name", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        if not name or not phone or not address:
            flash("Please fill in all fields.", "error")
            return render_template("checkout.html", items=items, total=total)

        if len(phone) != 10 or not phone.isdigit():
            flash("Phone number must contain exactly 10 digits.", "error")
            return render_template("checkout.html", items=items, total=total)

        # Check stock again before saving the order.
        conn = get_db()
        for item in items:
            current_book = conn.execute(
                "SELECT stock FROM books WHERE id = ?",
                (item["book"]["id"],)
            ).fetchone()

            if current_book is None or current_book["stock"] < item["quantity"]:
                conn.close()
                flash(f"Not enough stock for {item['book']['title']}.", "error")
                return redirect(url_for("cart"))

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save the main order first.
        cursor = conn.execute(
            """INSERT INTO orders
               (customer_name, phone, address, total, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (name, phone, address, total, created_at)
        )

        order_id = cursor.lastrowid

        # Save every book belonging to the order.
        for item in items:
            conn.execute(
                """INSERT INTO order_items
                   (order_id, book_id, quantity, price)
                   VALUES (?, ?, ?, ?)""",
                (
                    order_id,
                    item["book"]["id"],
                    item["quantity"],
                    item["book"]["price"]
                )
            )

            # Reduce stock after a successful order.
            conn.execute(
                "UPDATE books SET stock = stock - ? WHERE id = ?",
                (item["quantity"], item["book"]["id"])
            )

        conn.commit()
        conn.close()

        session["cart"] = {}

        return redirect(url_for("order_confirmation", order_id=order_id))

    return render_template("checkout.html", items=items, total=total)


@app.route("/order/<int:order_id>")
def order_confirmation(order_id):
    conn = get_db()

    order = conn.execute(
        "SELECT * FROM orders WHERE id = ?",
        (order_id,)
    ).fetchone()

    if order is None:
        conn.close()
        flash("Order not found.", "error")
        return redirect(url_for("home"))

    items = conn.execute(
        """SELECT order_items.quantity,
                  order_items.price,
                  books.title,
                  books.author
           FROM order_items
           JOIN books ON order_items.book_id = books.id
           WHERE order_items.order_id = ?""",
        (order_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "order.html",
        order=order,
        items=items
    )


@app.route("/orders")
def orders():
    conn = get_db()
    all_orders = conn.execute(
        "SELECT * FROM orders ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("orders.html", orders=all_orders)


if __name__ == "__main__":
    app.run(debug=True)
