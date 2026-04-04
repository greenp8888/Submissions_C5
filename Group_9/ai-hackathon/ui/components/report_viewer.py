from __future__ import annotations


def render_report(sections: list[dict]) -> str:
    return "\n\n".join(f"## {section['title']}\n\n{section['content']}" for section in sections)

