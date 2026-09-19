"""Gmail access for email-driven order intake (agent/email_intake.py).

Mirrors google_calendar.py's shape and shares the same OAuth connection
(agent/google_auth.py) — one "Connect Google Calendar" covers both. Every
function fails soft (None/[]) on missing auth or any API error, since
email intake is a background, best-effort process that must never crash
the rest of the app.
"""

import base64

from . import google_auth

try:
    from googleapiclient.errors import HttpError
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    HttpError = Exception


def _service():
    return google_auth.get_service("gmail", "v1")


def get_own_email_address():
    """The connected account's own address — lets email_intake.py tell "the
    owner said X" apart from "the customer said Y" in a thread."""
    service = _service()
    if service is None:
        return None
    try:
        profile = service.users().getProfile(userId="me").execute()
    except HttpError:
        return None
    return profile.get("emailAddress")


def list_candidate_messages(max_results: int = 20) -> list:
    """Recent inbox message ids/thread ids worth checking. Filtering out
    ones already handled (agent/db.py's processed_emails table) is the
    caller's job, not Gmail's."""
    service = _service()
    if service is None:
        return []
    try:
        result = (
            service.users()
            .messages()
            .list(userId="me", q="in:inbox newer_than:2d", maxResults=max_results)
            .execute()
        )
    except HttpError:
        return []
    return result.get("messages", [])


def _decode_body(data: str) -> str:
    try:
        return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")
    except (ValueError, UnicodeDecodeError):
        return ""


def _extract_plain_text(payload) -> str:
    """Walk a MIME payload for the first text/plain part; falls back to
    text/html (crude tag strip) if that's all there is."""
    if not payload:
        return ""

    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")

    if mime_type == "text/plain" and body_data:
        return _decode_body(body_data)

    html_fallback = None
    for part in payload.get("parts", []) or []:
        text = _extract_plain_text(part)
        if text:
            if part.get("mimeType") == "text/html" and html_fallback is None:
                html_fallback = text
            else:
                return text

    if mime_type == "text/html" and body_data and html_fallback is None:
        html_fallback = _decode_body(body_data)

    if html_fallback:
        import re
        return re.sub(r"<[^>]+>", " ", html_fallback)
    return ""


def get_message(message_id: str):
    """Fetch one message's headers (From/Subject) + decoded plain-text body,
    or None if not connected/found. Shape: {id, thread_id, from, subject, body}."""
    service = _service()
    if service is None:
        return None
    try:
        message = service.users().messages().get(userId="me", id=message_id, format="full").execute()
    except HttpError:
        return None

    payload = message.get("payload", {})
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
    return {
        "id": message.get("id"),
        "thread_id": message.get("threadId"),
        "from": headers.get("from", ""),
        "subject": headers.get("subject", ""),
        "body": _extract_plain_text(payload),
    }
