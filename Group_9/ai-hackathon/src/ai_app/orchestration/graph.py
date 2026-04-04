from __future__ import annotations

from langgraph.graph import END, StateGraph

from ai_app.orchestration.state import GraphState


def build_graph(planner, retriever, analysis, insight, reporter):
    graph = StateGraph(GraphState)
    graph.add_node("planner", planner)
    graph.add_node("retriever", retriever)
    graph.add_node("analysis", analysis)
    graph.add_node("insight", insight)
    graph.add_node("reporter", reporter)
    graph.set_entry_point("planner")
    graph.add_edge("planner", "retriever")
    graph.add_edge("retriever", "analysis")
    graph.add_edge("analysis", "insight")
    graph.add_edge("insight", "reporter")
    graph.add_edge("reporter", END)
    return graph.compile()
