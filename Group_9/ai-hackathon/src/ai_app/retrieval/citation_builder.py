from __future__ import annotations

from ai_app.domain.enums import SourceType
from ai_app.schemas.research import Source


SOURCE_PRIORITY = {
    SourceType.LOCAL_UPLOAD: 0,
    SourceType.PDF: 0,
    SourceType.WEB: 1,
    SourceType.NEWS: 2,
    SourceType.ACADEMIC: 3,
    SourceType.REPORT: 3,
    SourceType.API: 3,
}


def order_sources_for_citation(sources: list[Source]) -> list[Source]:
    return sorted(
        sources,
        key=lambda source: (SOURCE_PRIORITY[source.source_type], source.rank or 999),
    )


def format_inline_citations(sources: list[Source]) -> str:
    labels = []
    for source in order_sources_for_citation(sources):
        label = source.filename or source.title
        ref = f"{label} [{source.provider}]"
        if source.page_refs:
            ref += f" p.{','.join(str(page) for page in source.page_refs)}"
        if source.url:
            ref += f" <{source.url}>"
        labels.append(ref)
    return "; ".join(labels)


def format_reference_entry(source: Source) -> str:
    parts = [source.filename or source.title]
    parts.append(f"provider={source.provider}")
    parts.append(f"type={source.source_type.value}")
    parts.append(f"credibility={source.credibility_score:.2f}")
    parts.append(f"relevance={source.relevance_score:.2f}")
    if source.published_date:
        parts.append(f"published={source.published_date}")
    if source.url:
        parts.append(f"url={source.url}")
    if source.page_refs:
        parts.append(f"pages={','.join(str(page) for page in source.page_refs)}")
    if source.snippet:
        parts.append(f"snippet={source.snippet}")
    if source.credibility_explanation:
        parts.append(f"credibility_rationale={source.credibility_explanation}")
    return " | ".join(parts)
