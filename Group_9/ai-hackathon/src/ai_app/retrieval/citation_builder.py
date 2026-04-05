from __future__ import annotations

import re

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


def sanitize_report_text(text: str) -> str:
    text = text.replace("—", "-").replace("–", "-")
    cleaned_lines: list[str] = []
    for raw_line in text.replace("\r\n", "\n").splitlines():
        line = raw_line.strip()
        if not line:
            cleaned_lines.append("")
            continue
        if line.startswith("|") or re.match(r"^\|?[\s:-]+(\|[\s:-]+)+\|?$", line):
            continue
        line = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1", line)
        line = re.sub(r"https?://\S+", "", line)
        cleaned_lines.append(line.strip())
    normalized = "\n".join(cleaned_lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def build_reference_index(sources: list[Source]) -> dict[str, int]:
    return {source.id: index for index, source in enumerate(order_sources_for_citation(sources), start=1)}


def format_reference_link(source: Source, reference_index: int) -> str:
    label = str(reference_index)
    if source.url:
        return f"[{label}]({source.url})"
    return f"[{label}]"


def format_inline_citations(sources: list[Source], reference_index: dict[str, int] | None = None) -> str:
    labels = []
    for source in order_sources_for_citation(sources):
        if reference_index and source.id in reference_index:
            labels.append(format_reference_link(source, reference_index[source.id]))
        else:
            labels.append(source.filename or source.title)
    return "; ".join(labels)


def format_reference_entry(source: Source, reference_index: int | None = None) -> str:
    parts = [format_reference_link(source, reference_index) if reference_index is not None else (source.filename or source.title)]
    parts.append(source.filename or source.title)
    parts.append(f"provider={source.provider}")
    parts.append(f"type={source.source_type.value}")
    parts.append(f"credibility={source.credibility_score:.2f}")
    parts.append(f"relevance={source.relevance_score:.2f}")
    if source.published_date:
        parts.append(f"published={source.published_date}")
    if source.page_refs:
        parts.append(f"pages={','.join(str(page) for page in source.page_refs)}")
    if source.snippet:
        parts.append(f"snippet={sanitize_report_text(source.snippet)}")
    if source.credibility_explanation:
        parts.append(f"credibility_rationale={sanitize_report_text(source.credibility_explanation)}")
    return " | ".join(parts)
