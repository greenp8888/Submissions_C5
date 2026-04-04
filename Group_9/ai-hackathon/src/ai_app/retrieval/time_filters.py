from __future__ import annotations

from datetime import date, datetime


def parse_publication_date(value: str | None) -> date | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    for candidate in (normalized[:10], normalized):
        try:
            if len(candidate) == 10:
                return date.fromisoformat(candidate)
            return datetime.fromisoformat(candidate).date()
        except ValueError:
            continue
    return None


def matches_time_window(published_date: str | None, start_date: date | None, end_date: date | None) -> bool | None:
    if not start_date and not end_date:
        return True
    published = parse_publication_date(published_date)
    if not published:
        return None
    if start_date and published < start_date:
        return False
    if end_date and published > end_date:
        return False
    return True


def describe_date_window(start_date: date | None, end_date: date | None) -> str:
    if start_date and end_date:
        return f"{start_date.isoformat()} to {end_date.isoformat()}"
    if start_date:
        return f"since {start_date.isoformat()}"
    if end_date:
        return f"up to {end_date.isoformat()}"
    return "all time"


def expand_query_with_date_window(query: str, start_date: date | None, end_date: date | None) -> str:
    window = describe_date_window(start_date, end_date)
    if window == "all time":
        return query
    return f"{query} (focus on sources from {window})"
