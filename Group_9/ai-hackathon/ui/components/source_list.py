from __future__ import annotations


def render_sources(sources: list[dict]) -> str:
    return "\n".join(
        f"- [{source['title']}]({source['url']}) [{source['provider']}] ({source['source_type']})" if source.get("url")
        else f"- {source['title']} [{source['provider']}] ({source['source_type']})"
        for source in sources[:20]
    )
