from __future__ import annotations

from ai_app.schemas.research import Source


def dedupe_sources(sources: list[Source]) -> list[Source]:
    seen: dict[tuple[str, str], str] = {}
    deduped: list[Source] = []
    for source in sources:
        key = (source.title.strip().lower(), source.provider.strip().lower())
        if key in seen:
            source.duplicate_of_source_id = seen[key]
            continue
        seen[key] = source.id
        deduped.append(source)
    return deduped

