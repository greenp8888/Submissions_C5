from __future__ import annotations


def render_events(events: list[dict]) -> str:
    lines = []
    for event in events:
        prefix = f"[{event['event_type']}]"
        if event.get("agent"):
            prefix += f" [{event['agent']}]"
        message = event["message"]
        data = event.get("data") or {}
        if data.get("provider"):
            message += f" | provider={data['provider']}"
        if data.get("title"):
            message += f" | title={data['title']}"
        if data.get("filename"):
            message += f" | file={data['filename']}"
        if data.get("url"):
            message += f" | url={data['url']}"
        if data.get("sub_question"):
            message += f" | sub_question={data['sub_question']}"
        if data.get("credibility_score") is not None:
            message += f" | credibility={data['credibility_score']:.2f}"
        lines.append(f"{prefix} {message}")
    return "\n".join(lines)
