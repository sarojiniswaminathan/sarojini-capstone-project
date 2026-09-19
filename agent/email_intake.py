"""Email-driven order intake (plan.md Section 23: "the user provides the
goal, the agent determines the workflow" — here the goal isn't even typed,
it's read from her inbox).

Deliberately does NOT reuse agent.agent.make_client()'s chat-oriented
GeminiClient/Anthropic wiring: that client is bound to the chat system
prompt and has the chat tools attached, neither of which belongs in a
one-shot classification call. This module builds its own minimal AI caller
instead, reusing agent.agent's provider preference (Anthropic first) and
model defaults for consistency.

Every public function fails soft: no Google connection, no AI key, or any
single bad message must never stop the rest of a poll cycle, since this
runs unattended in a background loop (app.py).
"""

import json
import os
import re
import uuid

from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

try:
    import anthropic
except ModuleNotFoundError:  # pragma: no cover - optional if using Gemini only
    anthropic = None

try:
    import google.generativeai as genai
except ModuleNotFoundError:  # pragma: no cover - optional if using Anthropic only
    genai = None

from . import agent as agent_mod
from . import gmail_client
from . import google_calendar
from . import inventory
from . import orders as orders_mod

EXTRACTION_SYSTEM_PROMPT = """You classify and extract structured data from a single email in the \
inbox of a small custom tailoring business. The business owner's own email address is: {owner_email}

Return ONLY a single JSON object (no prose, no markdown fences) with exactly this shape:
{{
  "category": "new_order" | "order_reply" | "supplier_update" | "irrelevant",
  "customer": string or null,
  "garment": string or null,
  "description": string or null,
  "deadline": "YYYY-MM-DD" or null,
  "estimated_hours": number or null,
  "materials_mentioned": [{{"name": string, "color": string or null, "qty": number, "unit": string}}],
  "owner_decision": "accept" | "decline" | "unclear",
  "supplier_material_name": string or null,
  "supplier_qty": number or null
}}

Rules:
- "new_order": a customer describing/requesting a new garment or order, and the owner \
({owner_email}) has not clearly responded in this thread yet.
- "order_reply": the OWNER's own words (from {owner_email}) clearly accept or decline taking on \
an order in this thread — set owner_decision accordingly.
- "supplier_update": a fabric/material supplier confirming a purchase, delivery, or restock — \
fill only supplier_material_name/supplier_qty.
- "irrelevant": anything else (newsletters, unrelated correspondence, spam, etc).
- owner_decision is "unclear" whenever the thread does not contain a clear yes/no from the owner \
herself — never guess her intent from the customer's tone alone.
- Never invent a deadline, quantity, or material that isn't actually stated in the email.
"""


def _make_extraction_caller():
    """Returns callable(prompt: str) -> str, or None if no AI key is configured.
    Mirrors agent.agent.make_client()'s Anthropic-first preference."""
    if anthropic is not None and os.environ.get("ANTHROPIC_API_KEY"):
        client = anthropic.Anthropic()

        def call(prompt, owner_email):
            response = client.messages.create(
                model=agent_mod.ANTHROPIC_MODEL,
                max_tokens=800,
                system=EXTRACTION_SYSTEM_PROMPT.format(owner_email=owner_email),
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(block.text for block in response.content if block.type == "text")

        return call

    if genai is not None and os.environ.get("GEMINI_API_KEY"):
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])

        def call(prompt, owner_email):
            model = genai.GenerativeModel(
                model_name=os.environ.get("GEMINI_MODEL", "gemini-3.6-flash"),
                system_instruction=EXTRACTION_SYSTEM_PROMPT.format(owner_email=owner_email),
            )
            response = model.generate_content(prompt)
            return agent_mod.extract_text_from_response(response)

        return call

    return None


def _parse_json_response(text):
    text = (text or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None


def _extract_order_info(call, email_text, owner_email, thread_context=None):
    prompt = f"{thread_context}\n\n---\n\n{email_text}" if thread_context else email_text
    try:
        raw = call(prompt, owner_email)
    except Exception:
        return None
    return _parse_json_response(raw)


def _guess_customer_from_header(from_header):
    match = re.match(r'^\s*"?([^"<]+?)"?\s*<', from_header or "")
    if match:
        return match.group(1).strip()
    return (from_header or "").split("<")[0].strip() or "Unknown customer"


def _is_from_owner(message, owner_email):
    return bool(owner_email) and owner_email.lower() in (message.get("from") or "").lower()


def _already_processed(conn, message_id):
    return conn.execute(
        "SELECT 1 FROM processed_emails WHERE message_id = ?", (message_id,)
    ).fetchone() is not None


def _mark_processed(conn, message, classification, order_id=None):
    conn.execute(
        "INSERT OR REPLACE INTO processed_emails (message_id, thread_id, classification, order_id) "
        "VALUES (?, ?, ?, ?)",
        (message["id"], message["thread_id"], classification, order_id),
    )
    conn.commit()


def _apply_supplier_update(conn, info):
    name = info.get("supplier_material_name")
    qty = info.get("supplier_qty")
    if not name or not qty:
        return
    matches = inventory.find_materials(conn, name_contains=name)
    if not matches:
        return
    inventory.adjust_physical(conn, matches[0]["id"], qty, "Purchased (detected from supplier email)")


def _allocate_matched_materials(conn, project_id, materials):
    for item in materials:
        if not item.get("qty"):
            continue
        matches = inventory.find_materials(conn, name_contains=item.get("name"), color=item.get("color"))
        if matches:
            orders_mod.allocate_material(conn, project_id, matches[0]["id"], item["qty"])


def _handle_new_order(conn, info, message, owner_email):
    decision = info.get("owner_decision", "unclear")
    if decision == "decline":
        return None  # per the business decision: a decline leaves no order record

    customer = info.get("customer") or _guess_customer_from_header(message["from"])
    materials = info.get("materials_mentioned") or []
    order_id = f"ORD-EMAIL-{uuid.uuid4().hex[:6].upper()}"

    if decision == "accept":
        order_id, project_id = orders_mod.create_order(
            conn, order_id, customer=customer, order_type="date_restricted",
            garment=info.get("garment"), description=info.get("description"),
            deadline=info.get("deadline"), estimated_hours=info.get("estimated_hours"),
            confirmation_status="confirmed", source="email",
            source_email_thread_id=message["thread_id"],
        )
        _allocate_matched_materials(conn, project_id, materials)
        return order_id

    # unclear -> ask her directly via a real calendar invite instead of guessing
    order_id, _ = orders_mod.create_order(
        conn, order_id, customer=customer, order_type="date_restricted",
        garment=info.get("garment"), description=info.get("description"),
        deadline=info.get("deadline"), estimated_hours=info.get("estimated_hours"),
        confirmation_status="pending", source="email",
        source_email_thread_id=message["thread_id"], pending_materials=materials,
    )
    summary = f"Confirm new order — {customer}: {info.get('garment') or 'unspecified garment'}"
    description = (
        f"Detected from an email from {message['from']} (subject: {message['subject']}).\n\n"
        f"Garment: {info.get('garment') or 'unspecified'}\n"
        f"Deadline: {info.get('deadline') or 'not specified'}\n"
        f"Materials mentioned: {materials or 'none'}\n\n"
        "Accept this invite to take on the order, or decline to turn it down."
    )
    event_id = google_calendar.create_confirmation_invite(summary, description, owner_email)
    if event_id:
        conn.execute("UPDATE orders SET confirmation_event_id = ? WHERE id = ?", (event_id, order_id))
        conn.commit()
    return order_id


def _handle_thread_reply(conn, call, message, pending_order, owner_email):
    """A new message on a thread that already has a pending order attached.
    Only the owner's own reply can resolve it — a customer follow-up
    question on a still-pending thread changes nothing."""
    if not _is_from_owner(message, owner_email):
        return "irrelevant"

    text = f"From: {message['from']}\nSubject: {message['subject']}\n\n{message['body']}"
    context = (
        f"This message is a reply in the thread for a pending order request from "
        f"{pending_order['customer']} ({pending_order['garment'] or 'unspecified garment'}). "
        f"Determine only whether the owner ({owner_email}) is now accepting or declining it."
    )
    info = _extract_order_info(call, text, owner_email, thread_context=context)
    decision = (info or {}).get("owner_decision", "unclear")

    if decision == "accept":
        orders_mod.confirm_pending_order(conn, pending_order["id"])
        if pending_order["confirmation_event_id"]:
            google_calendar.delete_event(pending_order["confirmation_event_id"])
        return "order_reply"
    if decision == "decline":
        if pending_order["confirmation_event_id"]:
            google_calendar.delete_event(pending_order["confirmation_event_id"])
        orders_mod.discard_pending_order(conn, pending_order["id"])
        return "order_reply"
    return "irrelevant"


def poll_and_process(conn):
    """Fetch recent inbox messages, classify each, and act — creating
    orders, reserving materials, updating stock, or sending a calendar
    confirmation invite. No-ops entirely if Google or an AI key isn't
    configured yet."""
    if not google_calendar.is_connected():
        return
    call = _make_extraction_caller()
    if call is None:
        return
    owner_email = gmail_client.get_own_email_address()
    if not owner_email:
        return

    pending_by_thread = {
        row["source_email_thread_id"]: row
        for row in orders_mod.list_pending_orders(conn)
        if row["source_email_thread_id"]
    }

    for item in gmail_client.list_candidate_messages():
        message_id = item.get("id")
        if not message_id or _already_processed(conn, message_id):
            continue
        message = gmail_client.get_message(message_id)
        if message is None:
            continue

        try:
            pending_order = pending_by_thread.get(message["thread_id"])
            if pending_order is not None:
                classification = _handle_thread_reply(conn, call, message, pending_order, owner_email)
                _mark_processed(conn, message, classification, pending_order["id"])
                continue

            text = f"From: {message['from']}\nSubject: {message['subject']}\n\n{message['body']}"
            info = _extract_order_info(call, text, owner_email)
            if info is None:
                continue  # not marked processed — retried next cycle rather than silently dropped

            category = info.get("category", "irrelevant")
            order_id = None
            if category == "supplier_update":
                _apply_supplier_update(conn, info)
            elif category == "new_order":
                order_id = _handle_new_order(conn, info, message, owner_email)
            _mark_processed(conn, message, category, order_id)
        except Exception:
            # One malformed/unexpected email must never stop the rest of the cycle.
            continue


def check_pending_confirmations(conn):
    """For every order still awaiting her decision via a calendar invite,
    check whether she's responded yet and resolve it if so."""
    if not google_calendar.is_connected():
        return
    owner_email = gmail_client.get_own_email_address()
    if not owner_email:
        return

    for order in orders_mod.list_pending_orders(conn):
        event_id = order["confirmation_event_id"]
        if not event_id:
            continue
        response = google_calendar.get_invite_response(event_id, owner_email)
        if response == "accepted":
            orders_mod.confirm_pending_order(conn, order["id"])
            google_calendar.delete_event(event_id)
        elif response == "declined":
            google_calendar.delete_event(event_id)
            orders_mod.discard_pending_order(conn, order["id"])
        # tentative / needsAction / None -> still undecided, check again next cycle
