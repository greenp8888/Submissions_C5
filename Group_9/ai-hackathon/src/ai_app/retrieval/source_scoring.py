from __future__ import annotations

from ai_app.domain.enums import SourceType
from ai_app.schemas.research import Source


def credibility_for_source(source: Source) -> float:
    base = {
        SourceType.LOCAL_UPLOAD: 0.92,
        SourceType.PDF: 0.85,
        SourceType.ACADEMIC: 0.88,
        SourceType.NEWS: 0.68,
        SourceType.WEB: 0.6,
        SourceType.REPORT: 0.74,
        SourceType.API: 0.8,
    }[source.source_type]
    title_bonus = 0.04 if len(source.title) > 20 else 0.0
    return min(0.99, base + title_bonus)


def rank_sources(sources: list[Source]) -> list[Source]:
    ordered = sorted(
        sources,
        key=lambda src: (src.relevance_score, src.credibility_score, -len(src.page_refs)),
        reverse=True,
    )
    for index, source in enumerate(ordered, start=1):
        source.rank = index
    return ordered

