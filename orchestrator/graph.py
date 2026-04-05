from langgraph.graph import StateGraph, END
from orchestrator.state import IncidentState
from orchestrator.router import route_after_remediation
from agents.classifier import classify_logs
from agents.remediation import generate_remediations
from agents.cookbook import synthesize_cookbook
from agents.slack_notifier import send_slack_notifications
from agents.jira_ticket import create_jira_tickets


def _classifier_node(state: IncidentState) -> dict:
    return classify_logs(state)


def _remediation_node(state: IncidentState) -> dict:
    return generate_remediations(state)


def _cookbook_node(state: IncidentState) -> dict:
    return synthesize_cookbook(state)


def _slack_node(state: IncidentState) -> dict:
    return send_slack_notifications(state)


def _jira_node(state: IncidentState) -> dict:
    return create_jira_tickets(state)


def _route_after_remediation(state: IncidentState) -> list[str]:
    return route_after_remediation(state)


def build_graph():
    graph = StateGraph(IncidentState)

    # Add nodes
    graph.add_node("classifier", _classifier_node)
    graph.add_node("remediation", _remediation_node)
    graph.add_node("cookbook", _cookbook_node)
    graph.add_node("slack_notifier", _slack_node)
    graph.add_node("jira_ticket", _jira_node)

    # Linear: start -> classifier -> remediation
    graph.set_entry_point("classifier")
    graph.add_edge("classifier", "remediation")

    # Conditional fan-out after remediation
    graph.add_conditional_edges(
        "remediation",
        _route_after_remediation,
        {
            "cookbook": "cookbook",
            "slack_notifier": "slack_notifier",
            "jira_ticket": "jira_ticket",
        },
    )

    # Fan-out agents all go to END
    graph.add_edge("cookbook", END)
    graph.add_edge("slack_notifier", END)
    graph.add_edge("jira_ticket", END)

    return graph.compile()
