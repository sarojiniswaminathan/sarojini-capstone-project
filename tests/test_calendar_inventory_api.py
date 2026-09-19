import sqlite3

import pytest
from fastapi.testclient import TestClient

import app
import calendar_api
import inventory_api
from agent import google_auth, inventory
from agent import orders as orders_mod
from agent.db import get_connection, reset_db


@pytest.fixture(autouse=True)
def _isolate_google_calendar(tmp_path, monkeypatch):
    """Every test in this file must be unable to reach the real Google
    Calendar/Gmail API, even on a machine that has already completed the
    OAuth flow for real (a real token.json would otherwise make
    list_events/create_event/Gmail calls issue live requests against
    someone's actual account). Pointing TOKEN_PATH (shared by
    google_calendar.py and gmail_client.py via agent/google_auth.py) at a
    file that doesn't exist makes is_connected() False unconditionally."""
    monkeypatch.setattr(google_auth, "TOKEN_PATH", tmp_path / "unused-token.json")


def _patch_get_connection(monkeypatch, db_path):
    def get_conn():
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    monkeypatch.setattr(calendar_api, "get_connection", get_conn)
    monkeypatch.setattr(inventory_api, "get_connection", get_conn)


def test_calendar_events_flags_material_shortage(tmp_path, monkeypatch):
    db_path = tmp_path / "tailoring.db"
    conn = reset_db(db_path)
    inventory.add_material(conn, "MAT-SATIN", "Satin", "fabric", "m", 0.0, color="Red")
    _, project_id = orders_mod.create_order(
        conn, "ORD-100", customer="Test Customer", order_type="exploratory_sourcing",
        garment="Dress", deadline="2026-09-30", estimated_hours=5,
    )
    orders_mod.allocate_material(conn, project_id, "MAT-SATIN", 3.0)

    _patch_get_connection(monkeypatch, db_path)
    client = TestClient(app.app)

    response = client.get(
        "/calendar/events", params={"start": "2026-09-01T00:00:00", "end": "2026-10-15T00:00:00"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["connected"] is False
    deadline_events = [e for e in payload["events"] if e["id"] == "deadline-ORD-100"]
    assert len(deadline_events) == 1
    assert deadline_events[0]["shortage"] is True


def test_calendar_day_lists_due_orders_with_no_local_commitment_store(tmp_path, monkeypatch):
    """There's no local commitments table any more — with Google not
    connected, /calendar/day should report that plainly rather than serving
    stale local data or crashing."""
    db_path = tmp_path / "tailoring.db"
    conn = reset_db(db_path)
    orders_mod.create_order(
        conn, "ORD-200", customer="Someone", order_type="date_restricted",
        garment="Skirt", deadline="2026-09-25", estimated_hours=3,
    )

    _patch_get_connection(monkeypatch, db_path)
    client = TestClient(app.app)

    response = client.get("/calendar/day", params={"date": "2026-09-25"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["date"] == "2026-09-25"
    assert any(o["order_id"] == "ORD-200" for o in payload["due_orders"])
    assert payload["connected"] is False
    assert payload["commitments"] == []


def test_add_commitment_reports_not_connected_without_google(tmp_path, monkeypatch):
    db_path = tmp_path / "tailoring.db"
    reset_db(db_path)
    _patch_get_connection(monkeypatch, db_path)
    client = TestClient(app.app)

    response = client.post(
        "/commitments",
        json={
            "title": "Lab exam",
            "start_datetime": "2026-09-19T14:00:00",
            "end_datetime": "2026-09-19T16:00:00",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "not_connected"


def test_inventory_glance_and_adjust(tmp_path, monkeypatch):
    db_path = tmp_path / "tailoring.db"
    conn = reset_db(db_path)
    inventory.add_material(conn, "MAT-COTTON", "Cotton", "fabric", "m", 5.0, color="Black")

    _patch_get_connection(monkeypatch, db_path)
    client = TestClient(app.app)

    glance = client.get("/inventory/glance").json()
    assert any(m["id"] == "MAT-COTTON" and m["photo_url"] is None for m in glance["materials"])

    adjust = client.post("/inventory/MAT-COTTON/adjust", json={"delta": 1.5, "note": "found more"})
    assert adjust.status_code == 200
    assert adjust.json()["new_physical_qty"] == 6.5

    missing = client.post("/inventory/MAT-UNKNOWN/adjust", json={"delta": 1.0, "note": "x"})
    assert missing.status_code == 404


def test_get_connection_migrates_databases_predating_photo_path(tmp_path):
    """A DB created before materials.photo_path existed should still work
    via the startup migration in agent/db.py."""
    db_path = tmp_path / "tailoring.db"
    conn = reset_db(db_path)
    conn.execute(
        "CREATE TABLE materials_old AS "
        "SELECT id, name, category, color, unit, physical_qty, notes, created_at, updated_at FROM materials"
    )
    conn.execute("DROP TABLE materials")
    conn.execute("ALTER TABLE materials_old RENAME TO materials")
    conn.commit()
    conn.close()

    migrated_conn = get_connection(db_path)
    columns = {row["name"] for row in migrated_conn.execute("PRAGMA table_info(materials)").fetchall()}
    assert "photo_path" in columns
