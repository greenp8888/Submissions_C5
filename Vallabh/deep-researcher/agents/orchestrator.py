"""
=============================================================================
LangGraph Orchestrator
=============================================================================
Wires all agents into a StateGraph with conditional routing.

Flow:
  START → query_planner → retriever → analyzer → [conditional]
                                                    ├─ if gaps + rounds left → gap_filler → analyzer
                                                    └─ else → fact_checker → insight_generator → report_builder → END
=============================================================================
"""
from __future__ import annotations

import logging
from typing import Literal

from langgraph.graph import StateGraph, START, END

from state import ResearchState, create_initial_state
from agents.query_planner import plan_query
from agents.retriever import retrieve_sources
from agents.analyzer import analyze_sources
from agents.fact_checker import check_facts
from agents.insight_generator import generate_insights
from agents.gap_filler import fill_gaps
from agents.report_builder import build_report
from config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Conditional Routing
# =============================================================================

def route_after_analysis(state: ResearchState) -> Literal["fill_gaps", "proceed"]:
    """
    After analysis, decide whether to do additional retrieval for gaps.
    Only fills gaps if:
    - Critical gaps exist
    - Gap filling is enabled
    - We haven't exceeded max retrieval rounds
    """
    has_gaps = state.get("has_critical_gaps", False)
    round_num = state.get("retrieval_round", 0)
    max_rounds = settings.MAX_RETRIEVAL_ROUNDS

    if has_gaps and settings.ENABLE_GAP_FILLING and round_num < max_rounds:
        logger.info(f"🔀 Routing: GAP FILLING (round {round_num}/{max_rounds})")
        return "fill_gaps"
    else:
        logger.info("🔀 Routing: PROCEED to fact-checking")
        return "proceed"


# =============================================================================
# Finalize Node
# =============================================================================

def finalize(state: ResearchState) -> dict:
    """Final node — sets pipeline status."""
    errors = state.get("error_trace", [])
    status = "completed" if not errors else "completed_with_errors"

    sources_count = len(state.get("sources", []))
    report = state.get("report", {})

    logger.info(
        f"🏁 Pipeline {status}: "
        f"{sources_count} sources, "
        f"{len(state.get('fact_checks', []))} fact-checks, "
        f"{len(state.get('trends', []))} trends, "
        f"{len(state.get('hypotheses', []))} hypotheses, "
        f"report: {'generated' if report else 'missing'}"
    )

    return {
        "pipeline_status": status,
        "current_agent": "finalize",
    }


# =============================================================================
# Graph Construction
# =============================================================================

def build_graph() -> StateGraph:
    """Build and compile the research pipeline graph."""

    graph = StateGraph(ResearchState)

    # ── Add Nodes ──
    graph.add_node("query_planner", plan_query)
    graph.add_node("retriever", retrieve_sources)
    graph.add_node("analyzer", analyze_sources)
    graph.add_node("gap_filler", fill_gaps)
    graph.add_node("fact_checker", check_facts)
    graph.add_node("insight_generator", generate_insights)
    graph.add_node("report_builder", build_report)
    graph.add_node("finalize", finalize)

    # ── Edges ──
    graph.add_edge(START, "query_planner")
    graph.add_edge("query_planner", "retriever")
    graph.add_edge("retriever", "analyzer")

    # Conditional: gap filling loop
    graph.add_conditional_edges(
        "analyzer",
        route_after_analysis,
        {
            "fill_gaps": "gap_filler",
            "proceed": "fact_checker",
        },
    )
    # Gap filler loops back to analyzer for re-evaluation
    graph.add_edge("gap_filler", "analyzer")

    # Linear path after analysis
    graph.add_edge("fact_checker", "insight_generator")
    graph.add_edge("insight_generator", "report_builder")
    graph.add_edge("report_builder", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()


# =============================================================================
# Convenience: Run Pipeline
# =============================================================================

def run_pipeline(query: str, depth: str = "standard") -> ResearchState:
    """
    Execute the full research pipeline.

    Args:
        query: Research question
        depth: "quick" (3-4 sub-Q, fewer sources), "standard", "deep" (5-7 sub-Q, more sources)

    Returns:
        Final pipeline state with all results
    """
    logger.info("=" * 60)
    logger.info(f"🚀 Starting Deep Research Pipeline")
    logger.info(f"   Query: {query[:80]}...")
    logger.info(f"   Depth: {depth}")
    logger.info("=" * 60)

    state = create_initial_state(query, depth)
    graph = build_graph()
    final_state = graph.invoke(state)

    logger.info("=" * 60)
    logger.info(f"🏁 Pipeline complete: {final_state.get('pipeline_status', 'unknown')}")
    logger.info("=" * 60)

    return final_state
