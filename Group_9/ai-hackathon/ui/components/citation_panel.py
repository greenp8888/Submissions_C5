from __future__ import annotations


def render_citations(sources: list[dict]) -> str:
    return "\n".join(
        f"- {source['title']} | provider={source['provider']} | rank={source['rank']} | credibility={source['credibility_score']:.2f} | relevance={source['relevance_score']:.2f} | link={source.get('url') or 'local-only'}"
        for source in sources[:20]
    )
