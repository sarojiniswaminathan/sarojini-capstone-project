"""SQLite connection + schema setup for the Tailoring Business Agent MVP."""

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.sql"
DEFAULT_DB_PATH = Path(__file__).parent / "tailoring.db"


#  Columns added to tables that already existed in earlier versions of the
#  schema. CREATE TABLE IF NOT EXISTS (schema.sql) can't retrofit a new
#  column onto a table that's already there, so every connection checks and
#  migrates these on the fly. A brand-new table just needs adding to
#  schema.sql — CREATE TABLE IF NOT EXISTS handles that case on its own.
_ADDED_COLUMNS = {
    "materials": [("photo_path", "TEXT")],
    "orders": [
        ("confirmation_status", "TEXT NOT NULL DEFAULT 'confirmed'"),
        ("source", "TEXT NOT NULL DEFAULT 'chat'"),
        ("source_email_thread_id", "TEXT"),
        ("confirmation_event_id", "TEXT"),
        ("pending_materials_json", "TEXT"),
    ],
}


def _apply_column_migrations(conn: sqlite3.Connection) -> None:
    tables = {row["name"] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()}
    for table, columns in _ADDED_COLUMNS.items():
        if table not in tables:
            continue
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for name, sql_type in columns:
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}")
    conn.commit()


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Idempotent: creates any tables missing from an older database
    (CREATE TABLE IF NOT EXISTS) and migrates columns added to tables that
    already existed. Safe to call on every connection."""
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    _apply_column_migrations(conn)


def get_connection(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    _ensure_schema(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    _ensure_schema(conn)


def reset_db(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Delete and recreate the database file. Useful for demos/tests."""
    p = Path(db_path)
    if p.exists():
        p.unlink()
    conn = get_connection(db_path)
    init_db(conn)
    return conn
