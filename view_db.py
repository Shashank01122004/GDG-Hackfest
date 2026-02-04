"""Quick script to view demo.db contents."""
import sqlite3

conn = sqlite3.connect("demo.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

for table in tables:
    print(f"\n=== {table} ===")
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    print("  ", " | ".join(cols))
    for row in rows:
        print("  ", row)

conn.close()
print("\nDone.")
