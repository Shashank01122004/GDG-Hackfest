import sqlite3

conn = sqlite3.connect("demo.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT,
    city TEXT
)
""")

cursor.execute("""
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    amount REAL,
    order_date TEXT
)
""")

cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", [
    (1, "Amit", "amit@gmail.com", "Delhi"),
    (2, "Riya", "riya@gmail.com", "Mumbai"),
    (3, "John", None, "Bangalore")
])

cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", [
    (101, 1, 500.0, "2025-01-01"),
    (102, 2, 1200.0, "2025-01-10"),
    (103, 1, 300.0, "2025-01-15")
])

conn.commit()
conn.close()

print("Database created successfully.")
