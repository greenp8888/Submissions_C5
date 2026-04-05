"""Data models for retrieval results and the final research report.

Defines structured types for data returned by retrieval tools
and the compiled output from the Report Builder agent.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class RetrievalResult:
    """A single document chunk retrieved from a source.

    Attributes:
        source: The retrieval source identifier (e.g. "arxiv").
        title: Document or article title.
        url: Source URL or identifier.
        content: The retrieved text content.
        metadata: Additional source-specific metadata (authors, date, etc.).
        retrieved_at: ISO timestamp of when retrieval occurred.
    """

    source: str
    title: str
    url: str
    content: str
    metadata: dict = field(default_factory=dict)
    retrieved_at: str = ""

    def __post_init__(self) -> None:
        """Set timestamp to current UTC time if not provided."""
        if not self.retrieved_at:
            object.__setattr__(
                self, "retrieved_at", datetime.now(timezone.utc).isoformat()
            )


@dataclass
class AnalysisResult:
    """Output of the Critical Analysis agent.

    Attributes:
        summary: Synthesized summary of all retrieved findings.
        contradictions: List of conflicting claims across sources.
        validated_sources: URLs/IDs of sources deemed credible.
        source_quality_notes: Per-source credibility notes.
    """

    summary: str
    contradictions: list[str] = field(default_factory=list)
    validated_sources: list[str] = field(default_factory=list)
    source_quality_notes: dict[str, str] = field(default_factory=dict)


@dataclass
class ResearchReport:
    """The final compiled research report.

    Attributes:
        query: The original research question.
        sources_consulted: All source identifiers used.
        retrieval_count: Total number of documents retrieved.
        analysis_summary: The synthesized analysis.
        contradictions: Contradictions found across sources.
        insights: Generated hypotheses and trends.
        report_text: Full Markdown-formatted report text.
        success: Whether the pipeline completed successfully.
        urls_visited: All URLs retrieved during research.
    """

    query: str
    sources_consulted: list[str] = field(default_factory=list)
    retrieval_count: int = 0
    analysis_summary: str = ""
    contradictions: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    report_text: str = ""
    success: bool = False
    urls_visited: list[str] = field(default_factory=list)
