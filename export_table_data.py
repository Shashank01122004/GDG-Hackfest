"""
Export table row data to JSON.
Supports: all tables or selected tables; all rows or a limit per table;
one file per table or one combined file.
"""
import json
import sqlite3
from pathlib import Path
from typing import Optional

from config import ARTIFACTS_DIR, DB_PATH, DB_TYPE


def _export_sqlite(
    out_dir: Path,
    one_file: bool = False,
    tables: Optional[list[str]] = None,
    max_rows_per_table: Optional[int] = None,
):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if tables is None:
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cur.fetchall()]
    result = {}
    for table in tables:
        limit_sql = f" LIMIT {int(max_rows_per_table)}" if max_rows_per_table else ""
        cur.execute(f"SELECT * FROM [{table}]{limit_sql}")
        rows = [dict(row) for row in cur.fetchall()]
        result[table] = rows
        if not one_file:
            path = out_dir / f"{table}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2, default=str)
    conn.close()
    if one_file:
        path = out_dir / "table_data.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
    return result


def export_table_data_to_json(
    one_file: bool = False,
    tables: Optional[list[str]] = None,
    max_rows_per_table: Optional[int] = None,
) -> Path:
    """
    Export table row data to JSON.

    - one_file: If False, write artifacts/table_data/<table>.json per table.
                If True, write one artifacts/table_data/table_data.json with all tables.
    - tables: If None, export all tables. Else export only these table names.
    - max_rows_per_table: If None, export all rows. Else limit each table to this many rows.

    Returns the directory or file path written.
    """
    out_dir = ARTIFACTS_DIR / "table_data"
    if DB_TYPE != "sqlite":
        raise NotImplementedError("Table data export is supported only for SQLite.")
    _export_sqlite(
        out_dir,
        one_file=one_file,
        tables=tables,
        max_rows_per_table=max_rows_per_table,
    )
    return out_dir / "table_data.json" if one_file else out_dir
