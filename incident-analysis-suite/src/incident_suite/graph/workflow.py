from __future__ import annotations

from langgraph.graph import END, StateGraph

from incident_suite.agents.code_generator import code_generator_node
from incident_suite.agents.cookbook import cookbook_node
from incident_suite.agents.critical_analysis import critical_analysis_node
from incident_suite.agents.decomposer import decomposer_node
from incident_suite.agents.evidence import evidence_node
from incident_suite.agents.export_agent import export_agent_node
from incident_suite.agents.ingestion import ingestion_node
from incident_suite.agents.insight_generator import insight_generator_node
from incident_suite.agents.jira_agent import jira_ticket_node
from incident_suite.agents.normalizer import normalizer_node
from incident_suite.agents.notification import notification_node
from incident_suite.agents.orchestrator import orchestrator_node
from incident_suite.agents.planner import planner_node
from incident_suite.agents.qa import qa_node
from incident_suite.agents.report_builder import report_builder_node
from incident_suite.agents.retriever import retriever_node
from incident_suite.agents.self_correct import self_correct_node
from incident_suite.agents.verifier import verifier_node
from incident_suite.models.state import IncidentState


def build_workflow():
    graph = StateGraph(IncidentState)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("planner", planner_node)
    graph.add_node("decomposer", decomposer_node)
    graph.add_node("ingestion", ingestion_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("normalizer", normalizer_node)
    graph.add_node("evidence", evidence_node)
    graph.add_node("verifier", verifier_node)
    graph.add_node("critical_analysis", critical_analysis_node)
    graph.add_node("insight_generator", insight_generator_node)
    graph.add_node("code_generator", code_generator_node)
    graph.add_node("cookbook", cookbook_node)
    graph.add_node("report_builder", report_builder_node)
    graph.add_node("qa", qa_node)
    graph.add_node("self_correct", self_correct_node)
    graph.add_node("notification", notification_node)
    graph.add_node("jira_ticket", jira_ticket_node)
    graph.add_node("export_agent", export_agent_node)

    graph.set_entry_point("orchestrator")
    graph.add_edge("orchestrator", "planner")
    graph.add_edge("planner", "decomposer")
    graph.add_edge("decomposer", "ingestion")
    graph.add_edge("ingestion", "retriever")
    graph.add_edge("retriever", "normalizer")
    graph.add_edge("normalizer", "evidence")
    graph.add_edge("evidence", "verifier")
    graph.add_edge("verifier", "critical_analysis")
    graph.add_edge("critical_analysis", "insight_generator")
    graph.add_edge("insight_generator", "code_generator")
    graph.add_edge("code_generator", "cookbook")
    graph.add_edge("cookbook", "report_builder")
    graph.add_edge("report_builder", "qa")
    graph.add_conditional_edges(
        "qa",
        lambda state: "self_correct" if not state.get("qa_passed") else "notification",
        {"self_correct": "self_correct", "notification": "notification"},
    )
    graph.add_edge("self_correct", "report_builder")
    graph.add_conditional_edges(
        "notification",
        lambda state: "jira_ticket" if state.get("requires_jira") else "export_agent",
        {"jira_ticket": "jira_ticket", "export_agent": "export_agent"},
    )
    graph.add_edge("jira_ticket", "export_agent")
    graph.add_edge("export_agent", END)
    return graph.compile()
