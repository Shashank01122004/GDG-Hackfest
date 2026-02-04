"""
Extract schema metadata from the database: tables, columns, relationships, constraints.
Supports SQLite (full); PostgreSQL/SQL Server use same interface via db_connector.
"""
from config import DB_TYPE, ARTIFACTS_DIR
from db_connector import get_connection
from storage import save_json


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
            "nullable": bool(row[3] == 0),
            "primary_key": bool(row[5]),
        }
        for row in cursor.fetchall()
    ]


def _get_foreign_keys_sqlite(cursor, table_name):
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    return [
        {
            "from_column": row[3],
            "to_table": row[2],
            "to_column": row[4],
        }
        for row in cursor.fetchall()
    ]


def extract_metadata(db_path=None):
    """
    Extract full schema: tables, columns, and relationships (FKs).
    For SQLite, db_path is optional (uses config.DB_PATH).
    Returns: { "tables": { table_name: [columns] }, "relationships": [ { table, column, ref_table, ref_column } ] }
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if DB_TYPE == "sqlite":
            tables = _get_tables_sqlite(cursor)
            metadata = {"tables": {}, "relationships": []}
            for table_name in tables:
                metadata["tables"][table_name] = _get_columns_sqlite(cursor, table_name)
                for fk in _get_foreign_keys_sqlite(cursor, table_name):
                    metadata["relationships"].append({
                        "table": table_name,
                        "column": fk["from_column"],
                        "ref_table": fk["to_table"],
                        "ref_column": fk["to_column"],
                    })
        else:
            # Generic fallback: list tables and columns (implement per-DB if needed)
            metadata = {"tables": {}, "relationships": []}
            cursor.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            for table_name in tables:
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                """, (table_name,))
                metadata["tables"][table_name] = [
                    {
                        "column_name": row[0],
                        "data_type": row[1],
                        "nullable": row[2] == "YES",
                        "primary_key": False,
                    }
                    for row in cursor.fetchall()
                ]
    finally:
        conn.close()

    return metadata


def run_and_save():
    """Extract metadata and save to artifacts/metadata.json."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    meta = extract_metadata()
    path = ARTIFACTS_DIR / "metadata.json"
    save_json(meta, path)
    print(f"Saved metadata to {path}")
    return meta


if __name__ == "__main__":
    from config import ARTIFACTS_DIR
    run_and_save()
