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
        ref = source.title
        if source.page_refs:
            ref += f" p.{','.join(str(page) for page in source.page_refs)}"
        labels.append(ref)
    return "; ".join(labels)

