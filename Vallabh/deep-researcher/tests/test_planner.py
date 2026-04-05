"""Tests for Query Planner Agent."""
import pytest
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from state import create_initial_state, QueryPlan, SubQuestion
from agents.query_planner import plan_query


MOCK_PLAN = QueryPlan(
    original_query="What are the latest advances in quantum error correction?",
    research_scope="Covers recent QEC codes, hardware implementations, and path to fault tolerance",
    sub_questions=[
        SubQuestion(
            id=1, question="What are the main types of quantum error correction codes?",
            reasoning="Foundational understanding needed",
            search_keywords=["quantum error correction", "surface codes", "topological codes"],
            priority=1,
        ),
        SubQuestion(
            id=2, question="What recent breakthroughs have occurred in QEC (2023-2024)?",
            reasoning="Answers the recency aspect of the query",
            search_keywords=["quantum error correction breakthrough 2024", "below threshold QEC"],
            priority=1,
        ),
        SubQuestion(
            id=3, question="How close are we to fault-tolerant quantum computing?",
            reasoning="The practical implication question",
            search_keywords=["fault tolerant quantum computing timeline", "logical qubits milestone"],
            priority=2,
        ),
        SubQuestion(
            id=4, question="What are the current limitations and open problems?",
            reasoning="Identifies gaps and challenges",
            search_keywords=["quantum error correction challenges", "QEC overhead", "scalability"],
            priority=3,
        ),
    ],
    expected_source_types=["academic papers", "news articles", "research lab reports"],
)


class TestPlanQuery:
    """Test the query planner agent."""

    @patch("agents.query_planner.ChatOpenAI")
    @patch("agents.query_planner.ChatPromptTemplate")
    def test_successful_planning(self, mock_prompt_cls, mock_llm_cls):
        mock_structured_llm = MagicMock()
        mock_llm_instance = MagicMock()
        mock_llm_instance.with_structured_output.return_value = mock_structured_llm
        mock_llm_cls.return_value = mock_llm_instance

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = MOCK_PLAN
        mock_prompt = MagicMock()
        mock_prompt_cls.from_messages.return_value = mock_prompt
        mock_prompt.__or__ = MagicMock(return_value=mock_chain)

        state = create_initial_state("What are the latest advances in quantum error correction?")
        result = plan_query(state)

        assert len(result["sub_questions"]) == 4
        assert result["sub_questions"][0]["priority"] <= result["sub_questions"][-1]["priority"]
        assert result["current_agent"] == "query_planner"

    def test_empty_query(self):
        state = create_initial_state("")
        result = plan_query(state)
        assert result["sub_questions"] == []
        assert len(result["error_trace"]) > 0

    def test_whitespace_query(self):
        state = create_initial_state("   ")
        result = plan_query(state)
        assert result["sub_questions"] == []


class TestQueryPlanModel:
    """Test Pydantic model validation."""

    def test_valid_plan(self):
        assert len(MOCK_PLAN.sub_questions) == 4
        assert MOCK_PLAN.sub_questions[0].priority == 1

    def test_sub_question_serialization(self):
        d = MOCK_PLAN.sub_questions[0].model_dump()
        assert isinstance(d["search_keywords"], list)
        assert d["priority"] == 1

    def test_priority_bounds(self):
        with pytest.raises(Exception):
            SubQuestion(
                id=1, question="test", reasoning="test",
                search_keywords=["test"], priority=0,  # Below min
            )

        with pytest.raises(Exception):
            SubQuestion(
                id=1, question="test", reasoning="test",
                search_keywords=["test"], priority=6,  # Above max
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
