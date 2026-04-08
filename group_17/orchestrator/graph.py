from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from agents.log_classifier import classify_logs
from agents.remediation import generate_remediation
from agents.notification import send_slack_notification
from agents.cookbook import generate_cookbook
from agents.jira_agent import create_jira_tickets


class IncidentState(TypedDict):
    log_content: str
    classified_logs: Optional[dict]
    remediation: Optional[dict]
    notification: Optional[dict]
    cookbook: Optional[dict]
    jira_tickets: Optional[dict]
    current_step: str
    error: Optional[str]


def log_classifier_node(state: IncidentState) -> IncidentState:
    try:
        result = classify_logs(state["log_content"])
        return {
            **state,
            "classified_logs": result,
            "current_step": "log_classified"
        }
    except Exception as e:
        return {
            **state,
            "error": f"Log classifier failed: {str(e)}",
            "current_step": "error"
        }


def remediation_node(state: IncidentState) -> IncidentState:
    try:
        result = generate_remediation(state["classified_logs"])
        return {
            **state,
            "remediation": result,
            "current_step": "remediation_generated"
        }
    except Exception as e:
        return {
            **state,
            "error": f"Remediation agent failed: {str(e)}",
            "current_step": "error"
        }


def notification_node(state: IncidentState) -> IncidentState:
    try:
        result = send_slack_notification(
            state["classified_logs"],
            state["remediation"]
        )
        return {
            **state,
            "notification": result,
            "current_step": "notification_sent"
        }
    except Exception as e:
        return {
            **state,
            "error": f"Notification agent failed: {str(e)}",
            "current_step": "error"
        }


def cookbook_node(state: IncidentState) -> IncidentState:
    try:
        result = generate_cookbook(
            state["classified_logs"],
            state["remediation"]
        )
        return {
            **state,
            "cookbook": result,
            "current_step": "cookbook_generated"
        }
    except Exception as e:
        return {
            **state,
            "error": f"Cookbook agent failed: {str(e)}",
            "current_step": "error"
        }


def jira_node(state: IncidentState) -> IncidentState:
    try:
        result = create_jira_tickets(
            state["classified_logs"],
            state["remediation"]
        )
        return {
            **state,
            "jira_tickets": result,
            "current_step": "jira_tickets_created"
        }
    except Exception as e:
        return {
            **state,
            "error": f"JIRA agent failed: {str(e)}",
            "current_step": "error"
        }


def should_continue(state: IncidentState) -> str:
    if state.get("error"):
        return "error"
    return "continue"


def build_graph():
    workflow = StateGraph(IncidentState)

    workflow.add_node("log_classifier", log_classifier_node)
    workflow.add_node("remediation", remediation_node)
    workflow.add_node("notification", notification_node)
    workflow.add_node("cookbook", cookbook_node)
    workflow.add_node("jira", jira_node)

    workflow.set_entry_point("log_classifier")

    workflow.add_edge("log_classifier", "remediation")
    workflow.add_edge("remediation", "notification")
    workflow.add_edge("notification", "cookbook")
    workflow.add_edge("cookbook", "jira")
    workflow.add_edge("jira", END)

    return workflow.compile()


def run_incident_analysis(log_content: str) -> IncidentState:
    graph = build_graph()
    initial_state = IncidentState(
        log_content=log_content,
        classified_logs=None,
        remediation=None,
        notification=None,
        cookbook=None,
        jira_tickets=None,
        current_step="starting",
        error=None
    )
    result = graph.invoke(initial_state)
    return result