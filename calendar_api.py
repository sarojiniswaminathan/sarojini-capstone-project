"""HTTP endpoints for the calendar view and the Google Calendar connect flow.

The calendar is the business owner's actual Google Calendar (Section 14) —
there's no local commitments table to merge in. Order deadlines are still
local business data (from `orders`), shown alongside the live Google events.

Kept separate from app.py (which stays focused on the page + chat) since this
is purely additive surface area for the calendar feature.
"""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from agent import google_calendar
from agent import orders as orders_mod
from agent import planning
from agent.db import get_connection
from agent.scheduling import add_commitment

router = APIRouter()


class CommitmentRequest(BaseModel):
    title: str
    start_datetime: str
    end_datetime: str
    type: str = "personal"


@router.get("/auth/google/status")
async def google_status():
    return {"connected": google_calendar.is_connected()}


@router.get("/auth/google/login")
async def google_login():
    auth_url = google_calendar.get_auth_url()
    if auth_url is None:
        return {"error": "Google Calendar is not configured. Set GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET in .env."}
    return RedirectResponse(auth_url)


@router.post("/commitments")
async def create_commitment(payload: CommitmentRequest):
    conn = get_connection()
    event_id = add_commitment(conn, payload.title, payload.start_datetime, payload.end_datetime, payload.type)
    if event_id is None:
        return {"status": "not_connected", "message": "Connect Google Calendar first."}
    return {"status": "added", "google_event_id": event_id}


@router.get("/calendar/events")
async def calendar_events(start: str, end: str):
    """Feed for the calendar widget: live Google Calendar events + order
    deadlines (flagged with `shortage` when the order has a material
    shortfall). `connected: false` means there are no Google events to show
    yet, not that the range is genuinely empty."""
    conn = get_connection()
    connected = google_calendar.is_connected()
    events = []

    if connected:
        items = google_calendar.list_events(google_calendar.to_rfc3339(start), google_calendar.to_rfc3339(end))
        for item in items:
            start_info = item.get("start", {})
            end_info = item.get("end", {})
            events.append({
                "id": f"google-{item.get('id')}",
                "title": item.get("summary") or "(untitled)",
                "start": start_info.get("dateTime") or start_info.get("date"),
                "end": end_info.get("dateTime") or end_info.get("date"),
                "type": "google",
            })

    for order in orders_mod.list_orders(conn, exclude_completed=True):
        if not order["deadline"]:
            continue
        if not (start[:10] <= order["deadline"] <= end[:10]):
            continue
        shortages = planning.purchase_list(conn, order["id"])
        events.append({
            "id": f"deadline-{order['id']}",
            "title": f"Deadline: {order['id']} — {order['garment'] or order['customer']}",
            "start": order["deadline"],
            "end": order["deadline"],
            "type": "deadline",
            "shortage": bool(shortages),
            "order_id": order["id"],
        })

    return {"connected": connected, "events": events}


@router.get("/calendar/day")
async def calendar_day(date: str):
    """Day-details payload for the click-to-open panel — the day's plan,
    commitments (from Google Calendar), and any orders due with their
    shortage status."""
    conn = get_connection()
    connected = google_calendar.is_connected()
    plan = planning.daily_plan(conn, today=date)

    commitments = []
    if connected:
        items = google_calendar.list_events(
            google_calendar.to_rfc3339(f"{date}T00:00:00"), google_calendar.to_rfc3339(f"{date}T23:59:59")
        )
        commitments = google_calendar.events_as_intervals(items)

    due_orders = []
    for order in orders_mod.list_orders(conn, exclude_completed=True):
        if order["deadline"] != date:
            continue
        due_orders.append({
            "order_id": order["id"],
            "customer": order["customer"],
            "garment": order["garment"],
            "shortages": planning.purchase_list(conn, order["id"]),
        })

    return {"date": date, "connected": connected, "plan": plan, "commitments": commitments, "due_orders": due_orders}
