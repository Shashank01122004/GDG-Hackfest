import sqlite3

def profile_table(table, db_path="demo.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    total_rows = cursor.fetchone()[0]

    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()

    profile = {}

    for col in columns:
        col_name = col[1]
        cursor.execute(f"""
            SELECT 
                COUNT({col_name}),
                COUNT(DISTINCT {col_name})
            FROM {table}
        """)
        non_null, unique = cursor.fetchone()

        profile[col_name] = {
            "completeness": round((non_null / total_rows) * 100, 2) if total_rows else 0,
            "unique_values": unique
        }

    conn.close()
    return profile

print(profile_table("customers"))
