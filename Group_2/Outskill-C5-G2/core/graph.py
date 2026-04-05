"""
core/graph.py — LangGraph DAG Compilation

Wires all 5 agent nodes into a compiled, executable state machine.

Flow:
  START → planner → retriever → analyst → insight → reporter → END

Each node is a pure function (state) → state.
LLM is injected via functools.partial to keep node signatures clean.
"""

from functools import partial
from langgraph.graph import StateGraph, START, END

from core.state import ResearchState
from llm.openrouter import get_llm
from agents.planner import planner_node
from agents.retriever import retriever_node
from agents.analyst import analyst_node
from agents.insight import insight_node
from agents.reporter import report_builder_node


def build_research_graph(openrouter_api_key: str, model: str = "anthropic/claude-3.5-haiku"):
    """
    Builds and compiles the full LangGraph research pipeline.

    Uses functools.partial to inject the LLM into node functions,
    since LangGraph requires node functions to accept only (state).

    Args:
        openrouter_api_key : Your OpenRouter API key
        model              : Model string from OpenRouter

    Returns:
        Compiled LangGraph app (supports .invoke() and .stream())
    """
    llm = get_llm(api_key=openrouter_api_key, model=model)

    # Bind LLM to each node — partial makes signature: (state) → state
    planner   = partial(planner_node,        llm=llm)
    retriever = partial(retriever_node,      llm=llm)
    analyst   = partial(analyst_node,        llm=llm)
    insight   = partial(insight_node,        llm=llm)
    reporter  = partial(report_builder_node, llm=llm)

    builder = StateGraph(ResearchState)

    # Register all nodes
    builder.add_node("planner",   planner)
    builder.add_node("retriever", retriever)
    builder.add_node("analyst",   analyst)
    builder.add_node("insight",   insight)
    builder.add_node("reporter",  reporter)

    # Linear pipeline edges
    builder.add_edge(START,       "planner")
    builder.add_edge("planner",   "retriever")
    builder.add_edge("retriever", "analyst")
    builder.add_edge("analyst",   "insight")
    builder.add_edge("insight",   "reporter")
    builder.add_edge("reporter",  END)

    app = builder.compile()
    print("[Graph] Pipeline compiled: START → planner → retriever → analyst → insight → reporter → END")
    return app