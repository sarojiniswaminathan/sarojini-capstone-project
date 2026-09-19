"""Deterministic scheduling logic — plan.md Section 09.

The calendar is the business owner's actual Google Calendar (Section 14) —
there is no separate local commitments store to keep in sync. Every
commitment is read from and written directly to Google Calendar; if it isn't
connected yet, there's simply no commitment data (every day looks fully
free) until it is.
"""

from datetime import datetime, timedelta, date, time

from . import google_calendar

DEFAULT_WORK_WINDOW = (time(9, 0), time(21, 0))  # 9am-9pm, adjustable per call


def add_commitment(conn, title, start_datetime, end_datetime, type_="college"):
    """start_datetime/end_datetime: ISO strings, e.g. '2026-09-16T10:00:00'.
    Writes directly to the connected Google Calendar. Returns the created
    Google event id, or None if Google Calendar isn't connected."""
    return google_calendar.create_event(title, start_datetime, end_datetime)


def list_commitments(conn, start_range, end_range):
    """Commitments between start_range and end_range (ISO datetime strings)
    from the connected Google Calendar, shaped like
    {id, title, start_datetime, end_datetime}. Empty if not connected."""
    items = google_calendar.list_events(
        google_calendar.to_rfc3339(start_range), google_calendar.to_rfc3339(end_range)
    )
    return google_calendar.events_as_intervals(items)


def _parse_naive(dt_str):
    """This app doesn't model timezones anywhere, so a Google event's offset
    (if any) is dropped rather than compared against the naive work-window
    datetimes below."""
    dt = datetime.fromisoformat(dt_str)
    return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt


def _free_hours_on_day(conn, day: date, work_window=DEFAULT_WORK_WINDOW):
    """Free hours on a single calendar day, inside the work window, minus commitments."""
    day_start = datetime.combine(day, work_window[0])
    day_end = datetime.combine(day, work_window[1])
    commitments = list_commitments(conn, day_start.isoformat(), day_end.isoformat())

    # Build list of busy (start, end) intervals clipped to the work window, merged.
    intervals = []
    for c in commitments:
        c_start = max(_parse_naive(c["start_datetime"]), day_start)
        c_end = min(_parse_naive(c["end_datetime"]), day_end)
        if c_end > c_start:
            intervals.append((c_start, c_end))
    intervals.sort()
    merged = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    total_window = (day_end - day_start).total_seconds()
    busy = sum((e - s).total_seconds() for s, e in merged)
    free_seconds = max(0.0, total_window - busy)
    return free_seconds / 3600.0, merged


def available_hours_before(conn, deadline, start_from=None, work_window=DEFAULT_WORK_WINDOW):
    """Total free production hours between now (or start_from) and deadline (inclusive),
    day by day, respecting commitments. Returns (total_hours, [{date, free_hours}, ...])."""
    if isinstance(deadline, str):
        deadline = date.fromisoformat(deadline)
    start_day = start_from or date.today()
    if isinstance(start_day, str):
        start_day = date.fromisoformat(start_day)

    breakdown = []
    total = 0.0
    day = start_day
    while day <= deadline:
        free_hours, _ = _free_hours_on_day(conn, day, work_window)
        breakdown.append({"date": day.isoformat(), "free_hours": round(free_hours, 2)})
        total += free_hours
        day += timedelta(days=1)
    return round(total, 2), breakdown


def free_blocks_today(conn, today=None, work_window=DEFAULT_WORK_WINDOW):
    """Merged busy intervals + implied free gaps for today — used for daily planning."""
    today = today or date.today()
    if isinstance(today, str):
        today = date.fromisoformat(today)
    free_hours, busy_intervals = _free_hours_on_day(conn, today, work_window)
    day_start = datetime.combine(today, work_window[0])
    day_end = datetime.combine(today, work_window[1])

    gaps = []
    cursor = day_start
    for start, end in busy_intervals:
        if start > cursor:
            gaps.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < day_end:
        gaps.append((cursor, day_end))

    return {
        "date": today.isoformat(),
        "free_hours": round(free_hours, 2),
        "free_blocks": [
            {"start": s.strftime("%H:%M"), "end": e.strftime("%H:%M"),
             "hours": round((e - s).total_seconds() / 3600, 2)}
            for s, e in gaps
        ],
        "busy_blocks": [
            {"start": s.strftime("%H:%M"), "end": e.strftime("%H:%M")} for s, e in busy_intervals
        ],
    }


def conflict_check(conn, project_id, deadline, remaining_hours_needed):
    """Section 09 Conflict Detection: does enough free time exist before the deadline?"""
    available, breakdown = available_hours_before(conn, deadline)
    if remaining_hours_needed is None:
        return {"has_conflict": False, "available_hours": available, "needed_hours": None, "breakdown": breakdown}
    has_conflict = available < remaining_hours_needed
    return {
        "has_conflict": has_conflict,
        "available_hours": available,
        "needed_hours": remaining_hours_needed,
        "shortfall_hours": round(max(0.0, remaining_hours_needed - available), 2),
        "breakdown": breakdown,
    }
