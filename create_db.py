"""
Create a clean demo.db with proper schema and sample data.
Re-run to reset the database.
"""
import sqlite3
import os

DB_PATH = "demo.db"


def create_clean_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        city TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        order_date TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    )
    """)

    cursor.executemany(
        "INSERT INTO customers (name, email, city) VALUES (?, ?, ?)",
        [
            ("Amit", "amit@gmail.com", "Delhi"),
            ("Riya", "riya@gmail.com", "Mumbai"),
            ("John", "john@example.com", "Bangalore"),
        ],
    )

    cursor.executemany(
        "INSERT INTO orders (customer_id, amount, order_date) VALUES (?, ?, ?)",
        [
            (1, 500.0, "2025-01-01"),
            (2, 1200.0, "2025-01-10"),
            (1, 300.0, "2025-01-15"),
            (3, 750.0, "2025-01-20"),
        ],
    )

    conn.commit()
    conn.close()
    print("Database created successfully.")


if __name__ == "__main__":
    create_clean_db()
