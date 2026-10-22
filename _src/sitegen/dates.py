"""Dates as the site prints them ("8 September 2026", "7–11 October 2026")."""

import os
from datetime import date

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def parse(value: str) -> date:
    return date.fromisoformat(str(value)[:10])


def long(d: date) -> str:
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def span(start: date, end: date) -> str:
    """"7–11 October 2026", "30 September – 2 October 2026", or one day."""
    if end == start:
        return long(start)
    if (start.year, start.month) == (end.year, end.month):
        return f"{start.day}–{end.day} {MONTHS[end.month - 1]} {end.year}"
    if start.year == end.year:
        return f"{start.day} {MONTHS[start.month - 1]} – {long(end)}"
    return f"{long(start)} – {long(end)}"


def today() -> date:
    """Build date; SITE_TODAY=YYYY-MM-DD overrides it (for previews and tests)."""
    override = os.environ.get("SITE_TODAY")
    return parse(override) if override else date.today()
