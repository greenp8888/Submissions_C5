from __future__ import annotations


def render_citations(sources: list[dict]) -> str:
    if not sources:
        return "No references yet."
    sections = {
        "RAG References": [source for source in sources if source.get("provider") == "local_rag"],
        "Web References": [source for source in sources if source.get("provider") == "tavily" and source.get("source_type") == "web"],
        "News References": [source for source in sources if source.get("provider") == "tavily" and source.get("source_type") == "news"],
        "arXiv References": [source for source in sources if source.get("provider") == "arxiv"],
    }
    blocks: list[str] = []
    for title, items in sections.items():
        if not items:
            continue
        blocks.append(f"### {title}")
        for source in items[:20]:
            ref_title = source.get("filename") or source["title"]
            pages = f" | pages={','.join(str(page) for page in source.get('page_refs', []))}" if source.get("page_refs") else ""
            published = f" | published={source.get('published_date')}" if source.get("published_date") else ""
            blocks.append(
                f"- {ref_title} | provider={source['provider']} | rank={source['rank']} | credibility={source['credibility_score']:.2f} | relevance={source['relevance_score']:.2f}{pages}{published} | link={source.get('url') or 'local-only'}"
            )
            if source.get("snippet"):
                blocks.append(f"  snippet: {source['snippet']}")
            if source.get("credibility_explanation"):
                blocks.append(f"  rationale: {source['credibility_explanation']}")
    return "\n".join(blocks)
