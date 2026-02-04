"""
Database connector: SQLite (default), PostgreSQL, SQL Server.
Returns a connection object for metadata extraction and profiling.
"""
import sqlite3
from config import DB_TYPE, DB_PATH, POSTGRES_URI, SQLSERVER_URI


def get_connection():
    """Return a DB connection. SQLite supported out of the box."""
    if DB_TYPE == "sqlite":
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    if DB_TYPE == "postgres":
        try:
            import psycopg2
            uri = POSTGRES_URI or "postgresql://localhost/demo"
            return psycopg2.connect(uri)
        except ImportError:
            raise RuntimeError(
                "PostgreSQL support requires: pip install psycopg2-binary. "
                "Set POSTGRES_URI in .env."
            )
    if DB_TYPE == "sqlserver":
        try:
            import pyodbc
            conn_str = SQLSERVER_URI
            if not conn_str:
                raise ValueError("Set SQLSERVER_URI in .env for SQL Server.")
            return pyodbc.connect(conn_str)
        except ImportError:
            raise RuntimeError(
                "SQL Server support requires: pip install pyodbc. "
                "Set SQLSERVER_URI in .env."
            )
    raise ValueError(f"Unknown DB_TYPE: {DB_TYPE}. Use sqlite, postgres, or sqlserver.")


def get_cursor(conn):
    """Return a cursor. For SQLite/psycopg2 it's conn.cursor(). For pyodbc, conn.cursor()."""
    return conn.cursor()
