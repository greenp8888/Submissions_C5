def merge_stream_chunk(accumulated: dict, step: dict) -> dict:
    """Merge LangGraph stream_mode='updates' chunks into one view of final fields."""
    for _node_name, update in step.items():
        if not isinstance(update, dict):
            continue
        for k, v in update.items():
            if k == "sources" and isinstance(v, list):
                accumulated.setdefault("sources", []).extend(v)
            else:
                accumulated[k] = v
    return accumulated


def format_source_for_display(source: dict) -> str:
    """Format a source for display in the UI."""
    tool = str(source.get("tool") or "?")
    sid = str(source.get("id") or "?")
    body = (source.get("content") or "").strip()
    return f"**{sid}** — `{tool}`\n{body}"


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
