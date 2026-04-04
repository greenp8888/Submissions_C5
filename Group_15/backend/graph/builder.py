from langgraph.graph import StateGraph, END
from graph.state import GraphState
from graph.nodes.input_node import input_node
from graph.nodes.query_builder import query_builder
from graph.nodes.parallel_retrieval import parallel_retrieval
from graph.nodes.requirements_matcher import requirements_matcher
from graph.nodes.aggregator import aggregator
from graph.nodes.analysis import analysis
from graph.nodes.report_builder import report_builder


def build_graph():
    g = StateGraph(GraphState)

    g.add_node("input", input_node)
    g.add_node("query_builder", query_builder)
    g.add_node("retrieval", parallel_retrieval)
    g.add_node("matcher", requirements_matcher)
    g.add_node("aggregator", aggregator)
    g.add_node("analysis", analysis)
    g.add_node("report", report_builder)

    g.set_entry_point("input")

    g.add_conditional_edges(
        "input",
        lambda s: "query_builder" if not s.get("error") else END
    )

    g.add_edge("query_builder", "retrieval")
    g.add_edge("retrieval", "matcher")
    g.add_edge("matcher", "aggregator")
    g.add_edge("aggregator", "analysis")
    g.add_edge("analysis", "report")
    g.add_edge("report", END)

    return g.compile()
