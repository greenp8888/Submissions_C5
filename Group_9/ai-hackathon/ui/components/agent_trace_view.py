from __future__ import annotations


def render_trace(trace: list[dict]) -> str:
    return "\n".join(
        f"- {entry['agent']} :: {entry['step']} :: tokens={entry.get('token_estimate')}"
        for entry in trace
    )

