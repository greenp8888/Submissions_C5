"""Research graph — constructs and compiles the LangGraph StateGraph.

Defines all nodes, edges, and the conditional retry routing function.
The graph is the orchestration backbone: it wires together all 5 agents
and enforces the pipeline flow with a built-in retry loop for the Retriever.

Pipeline:
    Query Planner → Retriever → [retry? → Retriever] → Analyzer
    → Insight Generator → Report Builder → END
"""

import logging
from functools import partial
from typing import Literal

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from multi_agent_researcher.agents.analyzer import analyzer_node
from multi_agent_researcher.agents.insight_generator import insight_generator_node
from multi_agent_researcher.agents.query_planner import query_planner_node
from multi_agent_researcher.agents.report_builder import report_builder_node
from multi_agent_researcher.agents.retriever import retriever_node
from multi_agent_researcher.models.state import ResearchState

logger = logging.getLogger(__name__)

# Maximum retrieval attempts before forcing continuation
_MAX_RETRIEVAL_ATTEMPTS = 3

# Minimum number of documents required to pass to the Analyzer
_MIN_DOCS_THRESHOLD = 3


def route_after_retrieval(
    state: ResearchState,
) -> Literal["retry", "continue"]:
    """Conditional edge function — decides whether to retry retrieval.

    Checks two conditions:
    1. The total retrieved documents are below the minimum threshold.
    2. The number of attempts has not yet hit the cap.

    If both are true, routes back to the Retriever for another pass
    with potentially refined queries. Otherwise, continues to the Analyzer.

    Args:
        state: The current ResearchState after a retrieval round.

    Returns:
        "retry" if more retrieval is needed, "continue" otherwise.
    """
    docs = state.get("retrieved_documents", [])
    attempts = state.get("retrieval_attempts", 0)
    doc_count = len(docs)

    logger.info(
        "Routing after retrieval: docs=%d, attempts=%d (threshold=%d, max=%d)",
        doc_count,
        attempts,
        _MIN_DOCS_THRESHOLD,
        _MAX_RETRIEVAL_ATTEMPTS,
    )

    if doc_count < _MIN_DOCS_THRESHOLD and attempts < _MAX_RETRIEVAL_ATTEMPTS:
        logger.info("Routing: RETRY (insufficient docs)")
        return "retry"

    logger.info("Routing: CONTINUE to Analyzer")
    return "continue"


def build_research_graph(llm: ChatOpenAI) -> object:
    """Build and compile the complete multi-agent research StateGraph.

    Constructs the LangGraph StateGraph with:
    - 5 agent nodes (each wrapped with the shared LLM via functools.partial)
    - Direct edges for the linear pipeline stages
    - A conditional edge after the Retriever for retry logic

    Args:
        llm: The configured ChatOpenAI (OpenRouter) model instance,
             shared across all agent nodes.

    Returns:
        CompiledGraph: The compiled, runnable LangGraph StateGraph.
    """
    graph = StateGraph(ResearchState)

    # Bind the LLM to each node function using partial application.
    # LangGraph node functions receive (state) but our agents need (state, llm).
    graph.add_node("query_planner", partial(query_planner_node, llm=llm))
    graph.add_node("retriever", partial(retriever_node, llm=llm))
    graph.add_node("analyzer", partial(analyzer_node, llm=llm))
    graph.add_node("insight_generator", partial(insight_generator_node, llm=llm))
    graph.add_node("report_builder", partial(report_builder_node, llm=llm))

    # Entry point
    graph.set_entry_point("query_planner")

    # Linear edges (no branching)
    graph.add_edge("query_planner", "retriever")

    # Conditional edge: retry retrieval or continue to analysis
    graph.add_conditional_edges(
        "retriever",
        route_after_retrieval,
        {
            "retry": "retriever",
            "continue": "analyzer",
        },
    )

    # Remaining linear pipeline
    graph.add_edge("analyzer", "insight_generator")
    graph.add_edge("insight_generator", "report_builder")
    graph.add_edge("report_builder", END)

    compiled = graph.compile()
    logger.info(
        "Research graph compiled: 5 nodes, conditional retry edge (max=%d attempts)",
        _MAX_RETRIEVAL_ATTEMPTS,
    )
    return compiled
