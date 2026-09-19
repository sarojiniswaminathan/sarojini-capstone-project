"""Google Calendar access (plan.md Section 14) — both the business owner's
real calendar view and, via create_confirmation_invite, the RSVP-based
human-in-the-loop approval mechanism (Section 12) for orders detected by
email_intake.py.

Every function here fails soft — returns None/[]/False on missing config,
missing auth, or any API error — so the rest of the app (chat, scheduling,
the calendar view) behaves identically whether or not Google Calendar has
ever been connected. Nothing in the deterministic core should ever raise
because Google is unreachable or not yet linked.
"""

from datetime import datetime, timedelta

from . import google_auth

try:
    from googleapiclient.errors import HttpError
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    HttpError = Exception

CALENDAR_ID = "primary"


def is_connected() -> bool:
    return google_auth.is_connected()


def get_auth_url():
    return google_auth.get_auth_url()


def exchange_code(code: str) -> bool:
    return google_auth.exchange_code(code)


def _service():
    return google_auth.get_service("calendar", "v3")


def list_events(time_min: str, time_max: str) -> list:
    """time_min/time_max: RFC3339 datetimes. Returns [] if not connected or on error."""
    service = _service()
    if service is None:
        return []
    try:
        result = (
            service.events()
            .list(calendarId=CALENDAR_ID, timeMin=time_min, timeMax=time_max,
                  singleEvents=True, orderBy="startTime")
            .execute()
        )
    except HttpError:
        return []
    return result.get("items", [])


def create_event(summary: str, start: str, end: str, description: str = None):
    """start/end: ISO datetimes. Returns the created Google event id, or None."""
    service = _service()
    if service is None:
        return None
    body = {"summary": summary, "start": {"dateTime": start}, "end": {"dateTime": end}}
    if description:
        body["description"] = description
    try:
        created = service.events().insert(calendarId=CALENDAR_ID, body=body).execute()
    except HttpError:
        return None
    return created.get("id")


def create_deadline_event(summary: str, date_str: str, description: str = None):
    """All-day event, e.g. for an order deadline. date_str: ISO date (YYYY-MM-DD)."""
    service = _service()
    if service is None:
        return None
    body = {"summary": summary, "start": {"date": date_str}, "end": {"date": date_str}}
    if description:
        body["description"] = description
    try:
        created = service.events().insert(calendarId=CALENDAR_ID, body=body).execute()
    except HttpError:
        return None
    return created.get("id")


def create_confirmation_invite(summary: str, description: str, owner_email: str,
                                start: str = None, end: str = None):
    """A real Google Calendar invite used as the human-in-the-loop approval
    step (Section 12) for an order email_intake.py couldn't resolve on its
    own: the owner is added as an attendee (sendUpdates="all" so she's
    actually notified) and later responds Yes/No on the event itself, the
    same as any other calendar invite — get_invite_response reads that back.

    start/end default to a short near-term placeholder slot (next full hour,
    15 minutes) since Calendar requires a time even though this isn't a real
    production session. Returns the created event id, or None."""
    service = _service()
    if service is None:
        return None
    if start is None or end is None:
        slot_start = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        start = slot_start.isoformat()
        end = (slot_start + timedelta(minutes=15)).isoformat()
    body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": to_rfc3339(start)},
        "end": {"dateTime": to_rfc3339(end)},
        "attendees": [{"email": owner_email}],
    }
    try:
        created = (
            service.events()
            .insert(calendarId=CALENDAR_ID, body=body, sendUpdates="all")
            .execute()
        )
    except HttpError:
        return None
    return created.get("id")


def get_invite_response(event_id: str, owner_email: str):
    """The owner's RSVP on a confirmation invite: 'accepted' / 'declined' /
    'tentative' / 'needsAction', or None if not connected/found."""
    service = _service()
    if service is None or not event_id:
        return None
    try:
        event = service.events().get(calendarId=CALENDAR_ID, eventId=event_id).execute()
    except HttpError:
        return None
    for attendee in event.get("attendees", []):
        if attendee.get("self") or attendee.get("email", "").lower() == owner_email.lower():
            return attendee.get("responseStatus")
    return None


def delete_event(event_id: str) -> bool:
    service = _service()
    if service is None or not event_id:
        return False
    try:
        service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
    except HttpError:
        return False
    return True


def to_rfc3339(value: str) -> str:
    """Ensure a timezone designator is present, as the Calendar API requires.
    A bare naive datetime/date string (this app doesn't model timezones
    anywhere else either) is treated as already being in the caller's zone."""
    tail = value[10:]  # skip the "YYYY-MM-DD" date portion
    if value.endswith("Z") or "+" in tail or "-" in tail:
        return value
    return value + "Z"


def _extract_datetime(node):
    """A Google event's start/end node -> an ISO datetime string. All-day
    events (a bare "date", no "dateTime") are treated as starting/ending at
    midnight so they still sort/compare like every other commitment."""
    if not node:
        return None
    return node.get("dateTime") or (f"{node['date']}T00:00:00" if node.get("date") else None)


def events_as_intervals(items):
    """Convert list_events() items into the {title, start_datetime,
    end_datetime} shape the rest of the app already expects for a commitment."""
    result = []
    for item in items:
        start = _extract_datetime(item.get("start"))
        end = _extract_datetime(item.get("end"))
        if not start or not end:
            continue
        result.append({
            "id": item.get("id"),
            "title": item.get("summary") or "(untitled)",
            "start_datetime": start,
            "end_datetime": end,
        })
    return result
