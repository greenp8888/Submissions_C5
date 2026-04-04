from __future__ import annotations

from ai_app.domain.enums import SourceType
from ai_app.schemas.research import Source


SOURCE_TYPE_WEIGHT = {
    SourceType.LOCAL_UPLOAD: 0.95,
    SourceType.PDF: 0.9,
    SourceType.ACADEMIC: 0.92,
    SourceType.NEWS: 0.72,
    SourceType.WEB: 0.65,
    SourceType.REPORT: 0.78,
    SourceType.API: 0.84,
}

PROVIDER_WEIGHT = {
    "local_rag": 0.95,
    "arxiv": 0.92,
    "tavily": 0.74,
    "semantic_scholar": 0.9,
    "pubmed": 0.92,
    "newsapi": 0.7,
    "gdelt": 0.72,
}


def _metadata_completeness(source: Source) -> float:
    checks = [
        bool(source.title),
        bool(source.snippet),
        bool(source.url or source.filename),
        bool(source.published_date or source.page_refs),
        bool(source.provider),
    ]
    return sum(1 for value in checks if value) / len(checks)


def _time_window_score(source: Source) -> float:
    if source.matched_time_window is True:
        return 1.0
    if source.matched_time_window is False:
        return 0.45
    return 0.7


def credibility_details(source: Source, agreement_score: float = 0.6) -> tuple[float, str]:
    source_weight = SOURCE_TYPE_WEIGHT[source.source_type]
    provider_weight = PROVIDER_WEIGHT.get(source.provider.lower(), 0.68)
    metadata_score = _metadata_completeness(source)
    time_score = _time_window_score(source)
    agreement_score = max(0.0, min(1.0, agreement_score))
    score = (
        (source_weight * 0.35)
        + (provider_weight * 0.2)
        + (metadata_score * 0.15)
        + (time_score * 0.15)
        + (agreement_score * 0.15)
    )
    explanation = (
        f"Credibility heuristic combines source-type weight ({source_weight:.2f}), "
        f"provider trust ({provider_weight:.2f}), metadata completeness ({metadata_score:.2f}), "
        f"time-window fit ({time_score:.2f}), and cross-source agreement ({agreement_score:.2f})."
    )
    return min(0.99, round(score, 4)), explanation


def credibility_for_source(source: Source, agreement_score: float = 0.6) -> float:
    score, _ = credibility_details(source, agreement_score=agreement_score)
    return score


def rank_sources(sources: list[Source]) -> list[Source]:
    ordered = sorted(
        sources,
        key=lambda src: (src.relevance_score, src.credibility_score, src.matched_time_window is True, -len(src.page_refs)),
        reverse=True,
    )
    for index, source in enumerate(ordered, start=1):
        source.rank = index
    return ordered
