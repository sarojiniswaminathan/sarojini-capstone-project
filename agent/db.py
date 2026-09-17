"""SQLite connection + schema setup for the Tailoring Business Agent MVP."""

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "schema.sql"
DEFAULT_DB_PATH = Path(__file__).parent / "tailoring.db"


def get_connection(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.commit()


def reset_db(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Delete and recreate the database file. Useful for demos/tests."""
    p = Path(db_path)
    if p.exists():
        p.unlink()
    conn = get_connection(db_path)
    init_db(conn)
    return conn
