"""
Extract schema metadata from the database: tables, columns, relationships.
Works with CSV-created SQLite tables + real databases.
Automatically infers primary keys and foreign key relationships.
"""

from config import DB_TYPE, ARTIFACTS_DIR
from db_connector import get_connection
from storage import save_json


# --------------------------------------------------
# SQLite helpers
# --------------------------------------------------

def _get_tables_sqlite(cursor):
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return [row[0] for row in cursor.fetchall()]


def _get_columns_sqlite(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [
        {
            "column_name": row[1],
            "data_type": row[2],
            "nullable": row[3] == 0,
            "primary_key": bool(row[5]),
        }
        for row in cursor.fetchall()
    ]


def _get_foreign_keys_sqlite(cursor, table_name):
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    return [
        {
            "table": table_name,
            "column": row[3],
            "ref_table": row[2],
            "ref_column": row[4],
            "type": "explicit_fk",
        }
        for row in cursor.fetchall()
    ]


# --------------------------------------------------
# Intelligent inference
# --------------------------------------------------

def _infer_primary_keys(tables_schema):
    """
    Mark likely primary keys when CSV didn't define them.
    Rule: column named 'id' or ending with '_id'
    """
    for table, cols in tables_schema.items():
        for col in cols:
            name = col["column_name"].lower()
            if name == "id" or name.endswith("_id"):
                col["primary_key"] = True


def _infer_relationships(tables_schema):
    """
    Infer relationships by matching *_id columns to inferred PKs.
    """
    relations = []

    for table, cols in tables_schema.items():
        for col in cols:
            col_name = col["column_name"]

            if not col_name.lower().endswith("_id"):
                continue

            for target_table, target_cols in tables_schema.items():
                if target_table == table:
                    continue

                for tcol in target_cols:
                    if tcol["primary_key"] and tcol["column_name"] == col_name:
                        relations.append({
                            "table": table,
                            "column": col_name,
                            "ref_table": target_table,
                            "ref_column": col_name,
                            "type": "inferred_pk_match",
                        })

    return relations


# --------------------------------------------------
# Main extractor
# --------------------------------------------------

def extract_metadata():
    """
    Returns:
    {
      "tables": { table_name: [columns] },
      "relationships": [ { table, column, ref_table, ref_column, type } ]
    }
    """

    conn = get_connection()
    cursor = conn.cursor()

    metadata = {"tables": {}, "relationships": []}

    try:
        if DB_TYPE == "sqlite":
            tables = _get_tables_sqlite(cursor)

            # Extract columns
            for table in tables:
                metadata["tables"][table] = _get_columns_sqlite(cursor, table)

            # Infer missing PKs
            _infer_primary_keys(metadata["tables"])

            # Explicit FKs (if exist)
            for table in tables:
                metadata["relationships"].extend(
                    _get_foreign_keys_sqlite(cursor, table)
                )

            # Inferred relationships
            inferred = _infer_relationships(metadata["tables"])
            metadata["relationships"].extend(inferred)

        else:
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema='public'
            """)
            tables = [r[0] for r in cursor.fetchall()]

            for table in tables:
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema='public' AND table_name=%s
                """, (table,))

                metadata["tables"][table] = [
                    {
                        "column_name": r[0],
                        "data_type": r[1],
                        "nullable": r[2] == "YES",
                        "primary_key": False,
                    }
                    for r in cursor.fetchall()
                ]

    finally:
        conn.close()

    return metadata


# --------------------------------------------------
# Save runner
# --------------------------------------------------

def run_and_save():
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    meta = extract_metadata()
    path = ARTIFACTS_DIR / "metadata.json"
    save_json(meta, path)
    print(f"Saved metadata to {path}")
    return meta


if __name__ == "__main__":
    run_and_save()