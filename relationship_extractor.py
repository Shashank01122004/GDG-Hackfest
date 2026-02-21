import sqlite3


def detect_relationships(db_path="demo.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get tables
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tables = [row[0] for row in cursor.fetchall()]

    table_columns = {}

    # Collect schema info
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        cols = cursor.fetchall()
        table_columns[table] = {
            "columns": [c[1] for c in cols],
            "primary_keys": [c[1] for c in cols if c[5] == 1],
        }

    relationships = []

    # Infer relationships
    for table, info in table_columns.items():
        for col in info["columns"]:
            if col.endswith("_id"):
                for target_table, target_info in table_columns.items():
                    if target_table == table:
                        continue

                    # Check if column matches target PK
                    if col in target_info["primary_keys"]:
                        relationships.append({
                            "table": table,
                            "column": col,
                            "ref_table": target_table,
                            "ref_column": col,
                            "type": "inferred_pk_match"
                        })

    conn.close()
    return relationships