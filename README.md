# PageTurner Books

A simple online book store built using Python Flask, SQLite, HTML, CSS and JavaScript.

## Technologies

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript

## How to run

1. Open this project folder in VS Code.
2. Open the terminal.
3. Install Flask:

```bash
pip install flask
```

4. Create the database:

```bash
python init_db.py
```

5. Start the application:

```bash
python app.py
```

6. Open:

```text
http://127.0.0.1:5000
```

## Routes

- `/` - Shows all books and category filters. Runs SELECT queries on books.
- `/book/<id>` - Shows one book using SELECT by id.
- `/cart/add/<id>` - Adds a book to the Flask session cart.
- `/cart` - Shows cart items and calculates the total.
- `/cart/update/<id>` - Updates the quantity in the session cart.
- `/cart/remove/<id>` - Removes a book from the session cart.
- `/checkout` - Validates customer details and INSERTs an order and order items.
- `/order/<id>` - Shows order confirmation using a JOIN.
- `/orders` - Shows all placed orders.

## Database

There are three tables:

- books
- orders
- order_items

## Project flow

Browser -> Flask route -> SQLite -> Jinja template -> Browser

## Features

- Category filtering
- Live title/author search
- Book details
- Shopping cart
- Quantity update
- Remove confirmation
- 10-digit phone validation
- Checkout
- Order saving
- Stock reduction
- Order confirmation
- Responsive design
