"""
Data quality profiling: completeness, uniqueness, freshness, key health.
"""
from db_connector import get_connection
from config import ARTIFACTS_DIR
from storage import save_json


def _quote_sqlite(name):
    return f'"{name}"' if " " in name else name


def profile_table(cursor, table_name, columns):
    """Profile one table: completeness, unique counts, freshness (date cols), key health."""
    cursor.execute(f"SELECT COUNT(*) FROM {_quote_sqlite(table_name)}")
    total_rows = cursor.fetchone()[0]
    if total_rows == 0:
        return {"total_rows": 0, "columns": {}, "key_health": {"duplicate_pks": 0, "null_pks": 0}}

    col_names = [c["column_name"] for c in columns]
    pk_cols = [c["column_name"] for c in columns if c.get("primary_key")]
    column_stats = {}
    date_columns = []

    for c in columns:
        col_name = c["column_name"]
        try:
            cursor.execute(
                f"SELECT COUNT({_quote_sqlite(col_name)}), COUNT(DISTINCT {_quote_sqlite(col_name)}) FROM {_quote_sqlite(table_name)}"
            )
            non_null, distinct = cursor.fetchone()
        except Exception:
            non_null = distinct = 0
        completeness = round((non_null / total_rows) * 100, 2) if total_rows else 0
        column_stats[col_name] = {
            "completeness_pct": completeness,
            "unique_count": distinct,
            "null_count": total_rows - non_null,
        }
        # Detect date-like columns for freshness
        if c.get("data_type", "").upper() in ("TEXT", "DATE", "DATETIME", "TIMESTAMP"):
            if "date" in col_name.lower() or "time" in col_name.lower():
                date_columns.append(col_name)

    # Freshness: max/min for date columns
    freshness = {}
    for col in date_columns:
        try:
            cursor.execute(f"SELECT MIN({_quote_sqlite(col)}), MAX({_quote_sqlite(col)}) FROM {_quote_sqlite(table_name)}")
            row = cursor.fetchone()
            if row and row[0] and row[1]:
                freshness[col] = {"min": str(row[0]), "max": str(row[1])}
        except Exception:
            pass

    # Key health: null PKs, duplicate PKs
    key_health = {"null_pks": 0, "duplicate_pks": 0}
    if pk_cols:
        pk_expr = ", ".join(_quote_sqlite(c) for c in pk_cols)
        try:
            cursor.execute(f"SELECT COUNT(*) - COUNT({pk_expr}) FROM {_quote_sqlite(table_name)}")
            key_health["null_pks"] = cursor.fetchone()[0] or 0
            cursor.execute(
                f"SELECT COUNT(*) FROM (SELECT {pk_expr} FROM {_quote_sqlite(table_name)} GROUP BY {pk_expr} HAVING COUNT(*) > 1)"
            )
            key_health["duplicate_pks"] = cursor.fetchone()[0] or 0
        except Exception:
            pass

    return {
        "total_rows": total_rows,
        "columns": column_stats,
        "freshness": freshness,
        "key_health": key_health,
    }


def profile_all(metadata):
    """Profile every table in metadata. Expects metadata['tables']."""
    conn = get_connection()
    cursor = conn.cursor()
    profiles = {}
    try:
        tables = metadata.get("tables", metadata)
        for table_name, columns in tables.items():
            cols = columns if isinstance(columns, list) else []
            profiles[table_name] = profile_table(cursor, table_name, cols)
    finally:
        conn.close()
    return profiles


def run_and_save(metadata):
    """Load metadata from path or dict, profile all tables, save to artifacts/profiles.json."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    if isinstance(metadata, (str, __import__("pathlib").Path)):
        from storage import load_json
        metadata = load_json(metadata)
    # Normalize: allow metadata to be { "tables": { ... } } or legacy { "customers": [cols] }
    if "tables" not in metadata:
        metadata = {"tables": metadata}
    profiles = profile_all(metadata)
    path = ARTIFACTS_DIR / "profiles.json"
    save_json(profiles, path)
    print(f"Saved profiles to {path}")
    return profiles


if __name__ == "__main__":
    from metadata_extractor import extract_metadata
    meta = extract_metadata()
    run_and_save(meta)
