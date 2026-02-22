"""
Export table row data to JSON.
Supports: all tables or selected tables; all rows or a limit per table;
one file per table or one combined file; custom file name or prefix.
"""
import json
import re
import sqlite3
from pathlib import Path
from typing import Optional

from config import ARTIFACTS_DIR, DB_PATH, DB_TYPE


def _safe_filename(name: str) -> str:
    """Allow only alphanumeric, underscore, hyphen; no path separators."""
    if not name:
        return name
    return re.sub(r"[^\w\-]", "_", name.strip()).strip("_") or "export"


def _export_sqlite(
    out_dir: Path,
    one_file: bool = False,
    tables: Optional[list[str]] = None,
    max_rows_per_table: Optional[int] = None,
    custom_name: Optional[str] = None,
):
    base = _safe_filename(custom_name) if custom_name else None
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
            fname = f"{base}_{table}.json" if base else f"{table}.json"
            path = out_dir / fname
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2, default=str)
    conn.close()
    if one_file:
        fname = f"{base}.json" if base else "table_data.json"
        if not fname.endswith(".json"):
            fname += ".json"
        path = out_dir / fname
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
    return result


def export_table_data_to_json(
    one_file: bool = False,
    tables: Optional[list[str]] = None,
    max_rows_per_table: Optional[int] = None,
    custom_name: Optional[str] = None,
) -> Path:
    """
    Export table row data to JSON.

    - one_file: If False, write one file per table; if True, one combined file.
    - tables: If None, export all tables. Else export only these table names.
    - max_rows_per_table: If None, all rows. Else limit each table to this many rows.
    - custom_name: Optional. Single file: use as filename (e.g. "my_backup" -> my_backup.json).
                   Per-table: use as prefix (e.g. "my_backup" -> my_backup_customers.json, ...).

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
        custom_name=custom_name,
    )
    if one_file:
        base = _safe_filename(custom_name) if custom_name else "table_data"
        fname = f"{base}.json" if base else "table_data.json"
        if not fname.endswith(".json"):
            fname += ".json"
        return out_dir / fname
    return out_dir
