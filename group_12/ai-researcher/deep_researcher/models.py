
from __future__ import annotations

import operator
from typing import Annotated, TypedDict


class EvidenceItem(TypedDict):
    source_type: str
    source_label: str
    title: str
    url: str
    excerpt: str
    query_used: str
    relevance_hint: str


class ResearchState(TypedDict, total=False):
    question: str
    local_file_paths: list[str]
    enable_web_search: bool
    top_k: int
    web_results_per_query: int
    subquestions: list[str]
    queries: list[str]
    local_media_evidence: list[EvidenceItem]
    wikipedia_evidence: list[EvidenceItem]
    arxiv_evidence: list[EvidenceItem]
    tavily_evidence: list[EvidenceItem]
    evidence: list[EvidenceItem]
    analysis_summary: str
    contradictions: list[str]
    insights: list[str]
    final_report: str
    detailed_extracts_markdown: str
    retrieval_timing_local_media: dict[str, str]
    retrieval_timing_wikipedia: dict[str, str]
    retrieval_timing_arxiv: dict[str, str]
    retrieval_timing_tavily: dict[str, str]
    trace: list[str]
    retrieval_log: Annotated[list[str], operator.add]