"""
Configuration for Intelligent Data Dictionary Agent.
Uses environment variables with defaults for local demo.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

# Database: sqlite | postgres | sqlserver
DB_TYPE = os.getenv("DB_TYPE", "sqlite")
# SQLite: path to .db file; others: connection string
DB_PATH = os.getenv("DB_PATH", str(PROJECT_ROOT / "demo.db"))
# PostgreSQL: POSTGRES_URI; SQL Server: SQLSERVER_URI (optional for hackathon)
POSTGRES_URI = os.getenv("POSTGRES_URI", "")
SQLSERVER_URI = os.getenv("SQLSERVER_URI", "")

# AI: set OPENAI_API_KEY for business summaries and NL answers
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def get_db_connection_string():
    if DB_TYPE == "sqlite":
        return DB_PATH
    if DB_TYPE == "postgres":
        return POSTGRES_URI or "postgresql://localhost/demo"
    if DB_TYPE == "sqlserver":
        return SQLSERVER_URI or ""
    return DB_PATH
