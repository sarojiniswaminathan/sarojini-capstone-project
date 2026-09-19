import json

import pytest

from agent import email_intake, google_calendar, gmail_client, inventory
from agent import orders as orders_mod
from agent.db import reset_db


class _FakeMessages:
    def __init__(self, messages):
        self._by_id = {m["id"]: m for m in messages}

    def list_candidate_messages(self, max_results=20):
        return [{"id": message_id} for message_id in self._by_id]

    def get_message(self, message_id):
        return self._by_id.get(message_id)


@pytest.fixture
def conn(tmp_path):
    return reset_db(tmp_path / "tailoring.db")


@pytest.fixture(autouse=True)
def _connected(monkeypatch):
    # These tests are about the intake pipeline's own logic, not Google auth —
    # is_connected() is patched directly rather than pointing TOKEN_PATH at a
    # nonexistent file, since that would also make is_connected() False here.
    monkeypatch.setattr(google_calendar, "is_connected", lambda: True)


def _stub_gmail(monkeypatch, messages, owner_email="owner@example.com"):
    fake = _FakeMessages(messages)
    monkeypatch.setattr(gmail_client, "get_own_email_address", lambda: owner_email)
    monkeypatch.setattr(gmail_client, "list_candidate_messages", fake.list_candidate_messages)
    monkeypatch.setattr(gmail_client, "get_message", fake.get_message)


def _stub_extraction(monkeypatch, response_json):
    monkeypatch.setattr(
        email_intake, "_make_extraction_caller",
        lambda: (lambda prompt, owner_email: json.dumps(response_json)),
    )


def test_new_order_unclear_creates_pending_order_and_invite(monkeypatch, conn):
    _stub_gmail(monkeypatch, [{
        "id": "m1", "thread_id": "t1", "from": "Meera <meera@example.com>",
        "subject": "Dress order", "body": "I'd like a red dress for an event.",
    }])
    _stub_extraction(monkeypatch, {
        "category": "new_order", "customer": "Meera", "garment": "Dress",
        "description": "Red dress", "deadline": None, "estimated_hours": None,
        "materials_mentioned": [], "owner_decision": "unclear",
    })
    monkeypatch.setattr(
        google_calendar, "create_confirmation_invite",
        lambda summary, description, owner_email, start=None, end=None: "evt-1",
    )

    email_intake.poll_and_process(conn)

    pending = orders_mod.list_pending_orders(conn)
    assert len(pending) == 1
    assert pending[0]["customer"] == "Meera"
    assert pending[0]["confirmation_event_id"] == "evt-1"


def test_new_order_accept_creates_confirmed_order_with_no_invite(monkeypatch, conn):
    _stub_gmail(monkeypatch, [{
        "id": "m2", "thread_id": "t2", "from": "Priya <priya@example.com>",
        "subject": "Yes please", "body": "Please go ahead with the skirt order, deadline Oct 5.",
    }])
    _stub_extraction(monkeypatch, {
        "category": "new_order", "customer": "Priya", "garment": "Skirt",
        "description": None, "deadline": "2026-10-05", "estimated_hours": 4,
        "materials_mentioned": [], "owner_decision": "accept",
    })
    invite_calls = []
    monkeypatch.setattr(google_calendar, "create_confirmation_invite", lambda *a, **k: invite_calls.append(1))
    monkeypatch.setattr(google_calendar, "create_deadline_event", lambda *a, **k: None)

    email_intake.poll_and_process(conn)

    confirmed = orders_mod.list_orders(conn, confirmation_status="confirmed")
    assert len(confirmed) == 1
    assert confirmed[0]["customer"] == "Priya"
    assert invite_calls == []


def test_new_order_decline_creates_no_order(monkeypatch, conn):
    _stub_gmail(monkeypatch, [{
        "id": "m3", "thread_id": "t3", "from": "Owner <owner@example.com>",
        "subject": "Re: order", "body": "Sorry, I can't take this on.",
    }])
    _stub_extraction(monkeypatch, {
        "category": "new_order", "customer": "Someone", "garment": "Top",
        "description": None, "deadline": None, "estimated_hours": None,
        "materials_mentioned": [], "owner_decision": "decline",
    })

    email_intake.poll_and_process(conn)

    assert orders_mod.list_orders(conn, confirmation_status=None) == []


def test_supplier_update_adjusts_inventory(monkeypatch, conn):
    inventory.add_material(conn, "MAT-COTTON", "Cotton", "fabric", "m", 2.0, color="Black")
    _stub_gmail(monkeypatch, [{
        "id": "m4", "thread_id": "t4", "from": "Supplier <sales@fabricshop.com>",
        "subject": "Your order has shipped", "body": "5m of black cotton has been dispatched.",
    }])
    _stub_extraction(monkeypatch, {
        "category": "supplier_update", "customer": None, "garment": None,
        "description": None, "deadline": None, "estimated_hours": None,
        "materials_mentioned": [], "owner_decision": "unclear",
        "supplier_material_name": "Cotton", "supplier_qty": 5,
    })

    email_intake.poll_and_process(conn)

    summary = inventory.material_summary(conn, "MAT-COTTON")
    assert summary["physical_qty"] == 7.0


def test_processed_message_is_not_reprocessed(monkeypatch, conn):
    _stub_gmail(monkeypatch, [{
        "id": "m5", "thread_id": "t5", "from": "Someone <someone@example.com>",
        "subject": "Newsletter", "body": "50% off everything!",
    }])
    calls = []

    def _call(prompt, owner_email):
        calls.append(1)
        return json.dumps({"category": "irrelevant", "owner_decision": "unclear"})

    monkeypatch.setattr(email_intake, "_make_extraction_caller", lambda: _call)

    email_intake.poll_and_process(conn)
    email_intake.poll_and_process(conn)

    assert len(calls) == 1


def test_list_orders_default_excludes_pending(conn):
    orders_mod.create_order(
        conn, "ORD-PEND", customer="X", order_type="date_restricted", confirmation_status="pending",
    )
    orders_mod.create_order(conn, "ORD-OK", customer="Y", order_type="date_restricted")

    ids = {row["id"] for row in orders_mod.list_orders(conn)}
    assert ids == {"ORD-OK"}


def test_check_pending_confirmations_resolves_accepted_invite(monkeypatch, conn):
    order_id, _ = orders_mod.create_order(
        conn, "ORD-PEND2", customer="Z", order_type="date_restricted", confirmation_status="pending",
    )
    conn.execute("UPDATE orders SET confirmation_event_id = ? WHERE id = ?", ("evt-9", order_id))
    conn.commit()

    monkeypatch.setattr(gmail_client, "get_own_email_address", lambda: "owner@example.com")
    monkeypatch.setattr(google_calendar, "get_invite_response", lambda event_id, owner_email: "accepted")
    deleted = []
    monkeypatch.setattr(google_calendar, "delete_event", lambda event_id: deleted.append(event_id) or True)
    monkeypatch.setattr(google_calendar, "create_deadline_event", lambda *a, **k: None)

    email_intake.check_pending_confirmations(conn)

    order = orders_mod.get_order(conn, order_id)
    assert order["confirmation_status"] == "confirmed"
    assert deleted == ["evt-9"]


def test_check_pending_confirmations_discards_declined_invite(monkeypatch, conn):
    order_id, _ = orders_mod.create_order(
        conn, "ORD-PEND3", customer="W", order_type="date_restricted", confirmation_status="pending",
    )
    conn.execute("UPDATE orders SET confirmation_event_id = ? WHERE id = ?", ("evt-10", order_id))
    conn.commit()

    monkeypatch.setattr(gmail_client, "get_own_email_address", lambda: "owner@example.com")
    monkeypatch.setattr(google_calendar, "get_invite_response", lambda event_id, owner_email: "declined")
    monkeypatch.setattr(google_calendar, "delete_event", lambda event_id: True)

    email_intake.check_pending_confirmations(conn)

    assert orders_mod.get_order(conn, order_id) is None
