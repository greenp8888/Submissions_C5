"""Data models for research queries.

Defines the structured types for decomposed research queries
produced by the Query Planner agent.
"""

from dataclasses import dataclass, field
from typing import Literal

SourceType = Literal["arxiv", "tavily", "wikipedia", "serpapi", "pdf"]


@dataclass(frozen=True)
class SubQuery:
    """A single targeted retrieval sub-question.

    Attributes:
        question: The specific, retrieval-ready question.
        source: Which retrieval source this sub-query targets.
        priority: Importance ranking (1 = highest priority).
    """

    question: str
    source: SourceType
    priority: int = 1


@dataclass
class ResearchQuery:
    """A decomposed research query with all sub-questions.

    Produced by the Query Planner agent from the user's raw input.

    Attributes:
        original_query: The raw user question.
        sub_queries: Ordered list of targeted sub-questions.
        sources_to_use: Deduplicated list of source identifiers.
        research_type: Broad classification of the research task.
    """

    original_query: str
    sub_queries: list[SubQuery] = field(default_factory=list)
    sources_to_use: list[str] = field(default_factory=list)
    research_type: str = "general"

    def get_questions_for_source(self, source: str) -> list[str]:
        """Return all sub-questions targeting a specific source.

        Args:
            source: The source identifier (e.g. "arxiv").

        Returns:
            list[str]: Questions assigned to that source.
        """
        return [sq.question for sq in self.sub_queries if sq.source == source]
