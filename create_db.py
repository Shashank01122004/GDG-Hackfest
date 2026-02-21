import pandas as pd
import sqlite3
import os

DB = "demo.db"

CSV_FILES = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "products": "olist_products_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "sellers": "olist_sellers_dataset.csv"
}

conn = sqlite3.connect(DB)

for table, file in CSV_FILES.items():
    df = pd.read_csv(file)
    df.to_sql(table, conn, if_exists="replace", index=False)
    print(f"Loaded {table}")

conn.close()
print("Database created.")