"""Tests for LangGraph Orchestrator routing and graph structure."""
import pytest
from unittest.mock import patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from state import create_initial_state
from agents.orchestrator import route_after_analysis, finalize, build_graph


class TestRouteAfterAnalysis:
    """Test conditional routing after analysis."""

    def test_gaps_trigger_fill(self):
        state = create_initial_state("test")
        state["has_critical_gaps"] = True
        state["retrieval_round"] = 0

        with patch("agents.orchestrator.settings") as mock_settings:
            mock_settings.MAX_RETRIEVAL_ROUNDS = 2
            mock_settings.ENABLE_GAP_FILLING = True
            result = route_after_analysis(state)

        assert result == "fill_gaps"

    def test_no_gaps_proceeds(self):
        state = create_initial_state("test")
        state["has_critical_gaps"] = False
        state["retrieval_round"] = 0

        result = route_after_analysis(state)
        assert result == "proceed"

    def test_max_rounds_exceeded_proceeds(self):
        state = create_initial_state("test")
        state["has_critical_gaps"] = True
        state["retrieval_round"] = 3  # Exceeds max

        with patch("agents.orchestrator.settings") as mock_settings:
            mock_settings.MAX_RETRIEVAL_ROUNDS = 2
            mock_settings.ENABLE_GAP_FILLING = True
            result = route_after_analysis(state)

        assert result == "proceed"

    def test_gap_filling_disabled_proceeds(self):
        state = create_initial_state("test")
        state["has_critical_gaps"] = True
        state["retrieval_round"] = 0

        with patch("agents.orchestrator.settings") as mock_settings:
            mock_settings.MAX_RETRIEVAL_ROUNDS = 2
            mock_settings.ENABLE_GAP_FILLING = False
            result = route_after_analysis(state)

        assert result == "proceed"


class TestFinalize:
    def test_successful(self):
        state = create_initial_state("test")
        state["sources"] = [{"id": "1"}]
        state["report"] = {"title": "Test"}
        state["error_trace"] = []
        result = finalize(state)
        assert result["pipeline_status"] == "completed"

    def test_with_errors(self):
        state = create_initial_state("test")
        state["sources"] = []
        state["report"] = {}
        state["error_trace"] = ["Something broke"]
        result = finalize(state)
        assert result["pipeline_status"] == "completed_with_errors"


class TestGraphCompilation:
    def test_graph_builds(self):
        graph = build_graph()
        assert graph is not None

    def test_expected_nodes(self):
        graph = build_graph()
        graph_obj = graph.get_graph()
        node_ids = set(graph_obj.nodes.keys())

        expected = {
            "query_planner", "retriever", "analyzer", "gap_filler",
            "fact_checker", "insight_generator", "report_builder", "finalize",
            "__start__", "__end__",
        }
        assert expected.issubset(node_ids), f"Missing nodes: {expected - node_ids}"


class TestStateCreation:
    def test_defaults(self):
        state = create_initial_state("test query", "deep")
        assert state["query"] == "test query"
        assert state["depth"] == "deep"
        assert state["sources"] == []
        assert state["retrieval_round"] == 0
        assert state["pipeline_status"] == "initialized"
        assert state["has_critical_gaps"] is False

    def test_default_depth(self):
        state = create_initial_state("test")
        assert state["depth"] == "standard"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
