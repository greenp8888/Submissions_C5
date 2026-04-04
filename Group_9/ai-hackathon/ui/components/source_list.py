from __future__ import annotations


def render_sources(sources: list[dict]) -> str:
    if not sources:
        return "No sources collected yet."
    lines: list[str] = []
    for source in sources[:30]:
        title = source.get("filename") or source["title"]
        location = ""
        if source.get("page_refs"):
            pages = ",".join(str(page) for page in source["page_refs"])
            location = f" | pages={pages}"
        published = f" | published={source.get('published_date')}" if source.get("published_date") else ""
        credibility = f" | credibility={source['credibility_score']:.2f}"
        rationale = f"\n  rationale: {source.get('credibility_explanation')}" if source.get("credibility_explanation") else ""
        link = f"[{title}]({source['url']})" if source.get("url") else title
        lines.append(
            f"- {link} [{source['provider']}] ({source['source_type']}){location}{published}{credibility}{rationale}"
        )
    return "\n".join(lines)
