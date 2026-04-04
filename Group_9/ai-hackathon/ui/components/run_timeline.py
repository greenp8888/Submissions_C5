from __future__ import annotations


def render_events(events: list[dict]) -> str:
    return "\n".join(f"[{event['event_type']}] {event['message']}" for event in events)

