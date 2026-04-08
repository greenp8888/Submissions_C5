"""
=============================================================================
State Schema & Pydantic Models
=============================================================================
Central state definition for the LangGraph research pipeline.

Design:
- TypedDict for LangGraph state (required by StateGraph)
- Pydantic models for structured LLM output (validated, type-safe)
- Annotated[list, operator.add] for accumulative list fields
- Enums for source types and confidence levels
=============================================================================
"""
from __future__ import annotations

import operator
from datetime import datetime
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


# =============================================================================
# Enums
# =============================================================================

class SourceType(str, Enum):
    ARXIV = "ARXIV"
    WIKIPEDIA = "WIKIPEDIA"
    WEB = "WEB"
    NEWS = "NEWS"
    REPORT = "REPORT"
    API = "API"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"           # Multiple corroborating sources
    MEDIUM = "MEDIUM"       # Single credible source or partial corroboration
    LOW = "LOW"             # Single source, unverified, or speculative
    CONFLICTING = "CONFLICTING"  # Sources disagree


class ClaimStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    CONTRADICTED = "CONTRADICTED"


# =============================================================================
# Pydantic Models — Query Planning
# =============================================================================

class SubQuestion(BaseModel):
    """A decomposed sub-question from the original research query."""
    id: int = Field(..., description="Sequential ID starting from 1")
    question: str = Field(..., description="The specific sub-question to research")
    reasoning: str = Field(..., description="Why this sub-question is important for answering the main query")
    search_keywords: list[str] = Field(..., description="Suggested search keywords for retrieval")
    priority: int = Field(..., ge=1, le=5, description="Priority 1 (highest) to 5 (lowest)")


class QueryPlan(BaseModel):
    """Structured plan for researching a complex query."""
    original_query: str = Field(..., description="The original research question")
    research_scope: str = Field(..., description="Brief description of the research scope and boundaries")
    sub_questions: list[SubQuestion] = Field(..., description="Decomposed sub-questions to investigate")
    expected_source_types: list[str] = Field(
        default_factory=list,
        description="Types of sources expected to be useful (academic, news, reports, etc.)"
    )


# =============================================================================
# Pydantic Models — Retrieval
# =============================================================================

class Source(BaseModel):
    """A single retrieved source document."""
    id: str = Field(..., description="Unique source identifier (e.g., 'arxiv-001', 'wiki-003')")
    title: str = Field(..., description="Title of the source")
    source_type: SourceType = Field(..., description="Type of source")
    url: Optional[str] = Field(None, description="URL or DOI")
    authors: Optional[str] = Field(None, description="Authors if available")
    published_date: Optional[str] = Field(None, description="Publication date")
    content: str = Field(..., description="Extracted text content (truncated if needed)")
    relevance_score: float = Field(0.0, ge=0.0, le=1.0, description="Relevance to the query")
    sub_question_ids: list[int] = Field(default_factory=list, description="Which sub-questions this addresses")


class RetrievalResult(BaseModel):
    """Aggregated retrieval output."""
    sources: list[Source] = Field(default_factory=list)
    total_retrieved: int = Field(0)
    sources_by_type: dict[str, int] = Field(default_factory=dict)
    retrieval_summary: str = Field("", description="Brief summary of what was found")


# =============================================================================
# Pydantic Models — Analysis
# =============================================================================

class SourceSummary(BaseModel):
    """Summary of a single source's contributions."""
    source_id: str = Field(..., description="Reference to Source.id")
    key_findings: list[str] = Field(..., description="Main findings from this source")
    credibility: ConfidenceLevel = Field(..., description="Assessed credibility")
    credibility_reasoning: str = Field(..., description="Why this credibility was assigned")
    limitations: list[str] = Field(default_factory=list, description="Known limitations of this source")


class Contradiction(BaseModel):
    """A contradiction found between sources."""
    claim: str = Field(..., description="The claim that is contradicted")
    source_a_id: str = Field(..., description="First source ID")
    source_a_position: str = Field(..., description="What source A claims")
    source_b_id: str = Field(..., description="Second source ID")
    source_b_position: str = Field(..., description="What source B claims")
    resolution: Optional[str] = Field(None, description="Possible resolution or which is more credible")


class InformationGap(BaseModel):
    """An identified gap in the research."""
    description: str = Field(..., description="What information is missing")
    importance: str = Field(..., description="Why this gap matters")
    suggested_queries: list[str] = Field(default_factory=list, description="Queries to fill this gap")
    sub_question_id: Optional[int] = Field(None, description="Which sub-question this gap relates to")


class AnalysisResult(BaseModel):
    """Complete output from the Critical Analysis Agent."""
    source_summaries: list[SourceSummary] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    information_gaps: list[InformationGap] = Field(default_factory=list)
    consensus_findings: list[str] = Field(default_factory=list, description="Findings agreed upon by multiple sources")
    overall_assessment: str = Field("", description="Overall quality assessment of the research corpus")


# =============================================================================
# Pydantic Models — Fact Checking
# =============================================================================

class FactCheck(BaseModel):
    """Verification result for a specific claim."""
    claim: str = Field(..., description="The claim being verified")
    status: ClaimStatus = Field(..., description="Verification status")
    supporting_sources: list[str] = Field(default_factory=list, description="Source IDs that support this claim")
    contradicting_sources: list[str] = Field(default_factory=list, description="Source IDs that contradict this claim")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the verification")
    notes: str = Field("", description="Additional context about the verification")


class FactCheckResult(BaseModel):
    """Complete fact-checking output."""
    checks: list[FactCheck] = Field(default_factory=list)
    overall_reliability: float = Field(0.0, ge=0.0, le=1.0, description="Overall reliability score")
    reliability_summary: str = Field("", description="Summary of fact-checking results")


# =============================================================================
# Pydantic Models — Insights
# =============================================================================

class Trend(BaseModel):
    """An identified trend or pattern."""
    title: str = Field(..., description="Short trend title")
    description: str = Field(..., description="Detailed description of the trend")
    evidence: list[str] = Field(..., description="Source IDs and findings supporting this trend")
    confidence: ConfidenceLevel = Field(...)
    timeframe: Optional[str] = Field(None, description="Temporal scope of the trend")


class Hypothesis(BaseModel):
    """A generated hypothesis based on the evidence."""
    statement: str = Field(..., description="Clear hypothesis statement")
    reasoning_chain: list[str] = Field(..., description="Step-by-step reasoning leading to this hypothesis")
    supporting_evidence: list[str] = Field(..., description="Evidence supporting this hypothesis")
    counter_evidence: list[str] = Field(default_factory=list, description="Evidence that might weaken this hypothesis")
    testability: str = Field(..., description="How this hypothesis could be tested or validated")
    novelty: str = Field(..., description="What makes this hypothesis novel or interesting")


class InsightResult(BaseModel):
    """Complete output from the Insight Generation Agent."""
    trends: list[Trend] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    future_research_directions: list[str] = Field(default_factory=list)
    key_takeaways: list[str] = Field(default_factory=list, description="Top 3-5 takeaways")
    synthesis_narrative: str = Field("", description="Connecting narrative across all insights")


# =============================================================================
# Pydantic Models — Report
# =============================================================================

class ReportSection(BaseModel):
    """A section of the final research report."""
    heading: str
    content: str
    citations: list[str] = Field(default_factory=list, description="Source IDs cited in this section")


class ResearchReport(BaseModel):
    """The final structured research report."""
    title: str = Field(...)
    executive_summary: str = Field(...)
    methodology: str = Field(...)
    sections: list[ReportSection] = Field(default_factory=list)
    conclusions: str = Field(...)
    limitations: str = Field(...)
    references: list[str] = Field(default_factory=list)
    confidence_assessment: str = Field(...)
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


# =============================================================================
# LangGraph State
# =============================================================================

class ResearchState(TypedDict):
    """Central state for the LangGraph research pipeline."""

    # ── Input ──
    query: str                                              # Original research query
    depth: str                                              # "quick", "standard", "deep"

    # ── Query Planner ──
    query_plan: dict                                        # QueryPlan dict
    sub_questions: list[dict]                                # list of SubQuestion dicts

    # ── Retriever ──
    sources: Annotated[list[dict], operator.add]            # list of Source dicts
    retrieval_summary: str
    retrieval_round: int                                    # Current retrieval round

    # ── Analyzer ──
    source_summaries: Annotated[list[dict], operator.add]   # list of SourceSummary dicts
    contradictions: Annotated[list[dict], operator.add]     # list of Contradiction dicts
    information_gaps: list[dict]                             # list of InformationGap dicts
    consensus_findings: Annotated[list[str], operator.add]
    analysis_assessment: str

    # ── Fact Checker ──
    fact_checks: Annotated[list[dict], operator.add]        # list of FactCheck dicts
    overall_reliability: float
    reliability_summary: str

    # ── Insight Generator ──
    trends: Annotated[list[dict], operator.add]             # list of Trend dicts
    hypotheses: Annotated[list[dict], operator.add]         # list of Hypothesis dicts
    future_directions: Annotated[list[str], operator.add]
    key_takeaways: list[str]
    synthesis_narrative: str

    # ── Report Builder ──
    report: dict                                            # ResearchReport dict
    report_markdown: str                                    # Rendered markdown

    # ── Pipeline ──
    error_trace: Annotated[list[str], operator.add]
    pipeline_status: str
    current_agent: str
    has_critical_gaps: bool                                  # Triggers gap-filling loop


def create_initial_state(query: str, depth: str = "standard") -> ResearchState:
    """Factory function to create a properly initialized state."""
    return ResearchState(
        query=query,
        depth=depth,
        query_plan={},
        sub_questions=[],
        sources=[],
        retrieval_summary="",
        retrieval_round=0,
        source_summaries=[],
        contradictions=[],
        information_gaps=[],
        consensus_findings=[],
        analysis_assessment="",
        fact_checks=[],
        overall_reliability=0.0,
        reliability_summary="",
        trends=[],
        hypotheses=[],
        future_directions=[],
        key_takeaways=[],
        synthesis_narrative="",
        report={},
        report_markdown="",
        error_trace=[],
        pipeline_status="initialized",
        current_agent="none",
        has_critical_gaps=False,
    )
