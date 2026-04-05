"""Tests for Critical Analysis and Fact Checker Agents."""
import pytest
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from state import (
    create_initial_state, AnalysisResult, SourceSummary, Contradiction,
    InformationGap, ConfidenceLevel, FactCheckResult, FactCheck, ClaimStatus,
)
from agents.analyzer import analyze_sources, _format_sources_for_prompt
from agents.fact_checker import check_facts


SAMPLE_SOURCES = [
    {"id": "arxiv-001", "title": "QEC Advances", "source_type": "ARXIV",
     "content": "Recent work on surface codes...", "url": "https://arxiv.org/1",
     "authors": "Smith et al.", "published_date": "2024-06-01"},
    {"id": "web-001", "title": "Google QEC Milestone", "source_type": "WEB",
     "content": "Google achieved below-threshold QEC...", "url": "https://news.com/1"},
]

MOCK_ANALYSIS = AnalysisResult(
    source_summaries=[
        SourceSummary(
            source_id="arxiv-001",
            key_findings=["Surface codes achieving lower error rates", "New decoding algorithms"],
            credibility=ConfidenceLevel.HIGH,
            credibility_reasoning="Peer-reviewed academic paper",
            limitations=["Limited to superconducting qubits"],
        ),
        SourceSummary(
            source_id="web-001",
            key_findings=["Google demonstrated below-threshold QEC"],
            credibility=ConfidenceLevel.MEDIUM,
            credibility_reasoning="News article from reputable outlet",
            limitations=["May oversimplify technical details"],
        ),
    ],
    contradictions=[
        Contradiction(
            claim="Timeline to fault-tolerant QC",
            source_a_id="arxiv-001", source_a_position="5-10 years with current progress",
            source_b_id="web-001", source_b_position="Could be achieved within 3 years",
            resolution="Academic source is more conservative and likely more accurate",
        ),
    ],
    information_gaps=[
        InformationGap(
            description="No data on trapped-ion QEC approaches",
            importance="Major alternative hardware platform",
            suggested_queries=["trapped ion quantum error correction 2024"],
            sub_question_id=1,
        ),
    ],
    consensus_findings=["Surface codes are the leading approach for QEC"],
    overall_assessment="Good coverage of superconducting QEC, gaps in alternative approaches.",
)

MOCK_FACTCHECK = FactCheckResult(
    checks=[
        FactCheck(
            claim="Surface codes are the leading approach for QEC",
            status=ClaimStatus.VERIFIED,
            supporting_sources=["arxiv-001", "web-001"],
            contradicting_sources=[],
            confidence=0.92,
            notes="Confirmed by both academic and news sources",
        ),
        FactCheck(
            claim="Below-threshold QEC has been achieved",
            status=ClaimStatus.PARTIALLY_VERIFIED,
            supporting_sources=["web-001"],
            contradicting_sources=[],
            confidence=0.7,
            notes="Only one source confirms; awaiting peer review",
        ),
    ],
    overall_reliability=0.81,
    reliability_summary="Key claims well-supported; timeline claims need more corroboration.",
)


class TestFormatSources:
    def test_formats_correctly(self):
        formatted = _format_sources_for_prompt(SAMPLE_SOURCES)
        assert "arxiv-001" in formatted
        assert "web-001" in formatted
        assert "Smith et al." in formatted

    def test_empty_sources(self):
        result = _format_sources_for_prompt([])
        assert "No sources" in result


class TestAnalyzeSources:
    def test_no_sources(self):
        state = create_initial_state("test")
        result = analyze_sources(state)
        assert result["source_summaries"] == []
        assert result["has_critical_gaps"] is True

    @patch("agents.analyzer.ChatOpenAI")
    @patch("agents.analyzer.ChatPromptTemplate")
    def test_successful_analysis(self, mock_prompt_cls, mock_llm_cls):
        mock_structured_llm = MagicMock()
        mock_llm_instance = MagicMock()
        mock_llm_instance.with_structured_output.return_value = mock_structured_llm
        mock_llm_cls.return_value = mock_llm_instance

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MOCK_ANALYSIS
        mock_prompt = MagicMock()
        mock_prompt_cls.from_messages.return_value = mock_prompt
        mock_prompt.__or__ = MagicMock(return_value=mock_chain)

        state = create_initial_state("quantum error correction")
        state["sources"] = SAMPLE_SOURCES
        state["sub_questions"] = [{"id": 1, "question": "What is QEC?"}]

        result = analyze_sources(state)

        assert len(result["source_summaries"]) == 2
        assert len(result["contradictions"]) == 1
        assert len(result["information_gaps"]) == 1
        assert len(result["consensus_findings"]) == 1


class TestFactChecker:
    def test_no_findings(self):
        state = create_initial_state("test")
        result = check_facts(state)
        assert result["fact_checks"] == []
        assert result["overall_reliability"] == 0.0

    @patch("agents.fact_checker.ChatOpenAI")
    @patch("agents.fact_checker.ChatPromptTemplate")
    def test_successful_fact_check(self, mock_prompt_cls, mock_llm_cls):
        mock_structured_llm = MagicMock()
        mock_llm_instance = MagicMock()
        mock_llm_instance.with_structured_output.return_value = mock_structured_llm
        mock_llm_cls.return_value = mock_llm_instance

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MOCK_FACTCHECK
        mock_prompt = MagicMock()
        mock_prompt_cls.from_messages.return_value = mock_prompt
        mock_prompt.__or__ = MagicMock(return_value=mock_chain)

        state = create_initial_state("test")
        state["consensus_findings"] = ["Surface codes are leading"]
        state["source_summaries"] = [{"source_id": "arxiv-001", "key_findings": ["test"]}]
        state["sources"] = SAMPLE_SOURCES

        result = check_facts(state)

        assert len(result["fact_checks"]) == 2
        assert result["overall_reliability"] == 0.81


class TestPydanticModels:
    def test_confidence_levels(self):
        assert ConfidenceLevel.HIGH.value == "HIGH"
        assert ConfidenceLevel.CONFLICTING.value == "CONFLICTING"

    def test_claim_status(self):
        assert ClaimStatus.VERIFIED.value == "VERIFIED"
        assert ClaimStatus.CONTRADICTED.value == "CONTRADICTED"

    def test_fact_check_confidence_bounds(self):
        with pytest.raises(Exception):
            FactCheck(
                claim="test", status=ClaimStatus.VERIFIED,
                confidence=1.5,  # Invalid
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
