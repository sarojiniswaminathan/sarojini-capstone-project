import re
import sqlite3

from fastapi.testclient import TestClient

import app
from agent import inventory
from agent.db import reset_db


def test_direct_inventory_question_bypasses_ai(tmp_path, monkeypatch):
    db_path = tmp_path / "tailoring.db"
    conn = reset_db(db_path)
    inventory.add_material(
        conn,
        "MAT-001",
        "Cotton",
        "fabric",
        "m",
        physical_qty=12.0,
        color="Black",
    )

    def get_conn():
        new_conn = sqlite3.connect(str(db_path))
        new_conn.row_factory = sqlite3.Row
        new_conn.execute("PRAGMA foreign_keys = ON")
        return new_conn

    monkeypatch.setattr(app, "get_connection", get_conn)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    response = TestClient(app.app).post("/chat", json={"message": "How much black cotton do I have?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"]
    assert re.search(r"12(?:\.0)?|Cotton|Black", payload["reply"], re.IGNORECASE)
    assert payload["reply"].lower().find("no ai api key") == -1


def test_inventory_question_filters_to_requested_category(tmp_path, monkeypatch):
    db_path = tmp_path / "tailoring.db"
    conn = reset_db(db_path)
    inventory.add_material(conn, "MAT-COTTON", "Cotton", "fabric", "m", 12.0, color="Black")
    inventory.add_material(conn, "MAT-ZIP", "Zip", "fastening", "pieces", 8.0)
    inventory.add_material(conn, "MAT-THREAD", "Thread", "construction", "spool", 2.0)

    def get_conn():
        new_conn = sqlite3.connect(str(db_path))
        new_conn.row_factory = sqlite3.Row
        new_conn.execute("PRAGMA foreign_keys = ON")
        return new_conn

    monkeypatch.setattr(app, "get_connection", get_conn)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    client = TestClient(app.app)
    fabric_reply = client.post("/chat", json={"message": "How much fabric do I have?"}).json()["reply"]
    zipper_reply = client.post("/chat", json={"message": "How many zippers do I have?"}).json()["reply"]

    assert "Cotton" in fabric_reply
    assert "Zip" not in fabric_reply
    assert "Thread" not in fabric_reply
    assert "Zip" in zipper_reply
    assert "Cotton" not in zipper_reply
    assert "Thread" not in zipper_reply
