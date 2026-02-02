import sqlite3

def extract_metadata(db_path="demo.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    metadata = {}

    for (table_name,) in tables:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        metadata[table_name] = []
        for col in columns:
            metadata[table_name].append({
                "column_name": col[1],
                "data_type": col[2],
                "nullable": not col[3],
                "primary_key": bool(col[5])
            })

    conn.close()
    return metadata


if __name__ == "__main__":
    meta = extract_metadata()
    for table, cols in meta.items():
        print(f"\nTable: {table}")
        for c in cols:
            print(c)

from storage import save_metadata

meta = extract_metadata()
save_metadata(meta)
