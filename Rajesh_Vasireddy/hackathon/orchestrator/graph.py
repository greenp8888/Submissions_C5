"""LangGraph StateGraph definition for the incident pipeline."""

from __future__ import annotations

import dataclasses
import logging
from typing import Any

from langgraph.graph import END, StateGraph

from agents.cookbook import CookbookAgent
from agents.jira_agent import JiraAgent
from agents.log_classifier import LogClassifierAgent, LogReport
from agents.notification import NotificationAgent
from agents.remediation import RemediationAgent, RemediationPlan
from orchestrator.state import IncidentState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Node functions (each receives the full state and returns a partial update)
# ---------------------------------------------------------------------------


def classify_node(state: IncidentState) -> dict[str, Any]:
    """Run :class:`~agents.log_classifier.LogClassifierAgent` and store the result in state."""
    logger.info("[classify] Starting log classification for run_id=%s", state.get("run_id"))
    agent = LogClassifierAgent()
    try:
        report: LogReport = agent.run(state["raw_log"])
        return {
            "log_report": dataclasses.asdict(report),
            "current_step": "classify",
            "completed_steps": state.get("completed_steps", []) + ["classify"],
        }
    except Exception as exc:
        logger.error("[classify] Error: %s", exc)
        return {"errors": state.get("errors", []) + [str(exc)], "current_step": "classify", "finished": True}


def remediate_node(state: IncidentState) -> dict[str, Any]:
    """Run :class:`~agents.remediation.RemediationAgent` and store the plan in state."""
    if state.get("finished"):
        return {}
    logger.info("[remediate] Building remediation plan")
    agent = RemediationAgent()
    report_dict = state.get("log_report")
    if not report_dict:
        logger.error("[remediate] Missing log_report in state")
        return {"errors": state.get("errors", []) + ["Missing log_report from classify step"], "finished": True}
    report = LogReport(**report_dict)
    try:
        plan: RemediationPlan = agent.run(report)
        return {
            "remediation_plan": dataclasses.asdict(plan),
            "current_step": "remediate",
            "completed_steps": state.get("completed_steps", []) + ["remediate"],
        }
    except Exception as exc:
        logger.error("[remediate] Error: %s", exc)
        return {"errors": state.get("errors", []) + [str(exc)], "current_step": "remediate", "finished": True}


def cookbook_node(state: IncidentState) -> dict[str, Any]:
    """Run :class:`~agents.cookbook.CookbookAgent` and store the runbook markdown in state."""
    if state.get("finished"):
        return {}
    logger.info("[cookbook] Generating runbook markdown")
    agent = CookbookAgent()
    plan_dict = state.get("remediation_plan")
    if not plan_dict or not plan_dict.get("incident_type") or not plan_dict.get("severity"):
        logger.error("[cookbook] Missing remediation_plan or required fields in state")
        return {"errors": state.get("errors", []) + ["Missing remediation_plan from remediate step"], "finished": True}
    
    plan = RemediationPlan(**{k: v for k, v in plan_dict.items() if k in RemediationPlan.__dataclass_fields__})

    # Rebuild step objects
    from agents.remediation import RemediationStep
    plan.steps = [RemediationStep(**s) for s in plan_dict.get("steps", [])]

    try:
        md = agent.run(plan)
        return {
            "cookbook_md": md,
            "current_step": "cookbook",
            "completed_steps": state.get("completed_steps", []) + ["cookbook"],
        }
    except Exception as exc:
        logger.error("[cookbook] Error: %s", exc)
        return {"errors": state.get("errors", []) + [str(exc)], "current_step": "cookbook", "finished": True}


def notify_node(state: IncidentState) -> dict[str, Any]:
    """Run :class:`~agents.notification.NotificationAgent`; sets ``slack_sent`` in state."""
    if state.get("finished"):
        return {}
    logger.info("[notify] Sending Slack notification if applicable")
    agent = NotificationAgent()
    report_dict = state.get("log_report")
    if not report_dict:
        logger.error("[notify] Missing log_report in state")
        return {"errors": state.get("errors", []) + ["Missing log_report from classify step"], "finished": True}
    report = LogReport(**report_dict)
    try:
        sent = agent.run(report, cookbook_md=state.get("cookbook_md", ""))
        return {
            "slack_sent": sent,
            "current_step": "notify",
            "completed_steps": state.get("completed_steps", []) + ["notify"],
        }
    except Exception as exc:
        logger.error("[notify] Error: %s", exc)
        return {"errors": state.get("errors", []) + [str(exc)], "current_step": "notify", "slack_sent": False}


def jira_node(state: IncidentState) -> dict[str, Any]:
    """Run :class:`~agents.jira_agent.JiraAgent`; sets ``jira_ticket`` and ``finished`` in state."""
    if state.get("finished"):
        return {}
    logger.info("[jira] Creating JIRA ticket if CRITICAL")
    agent = JiraAgent()
    report_dict = state.get("log_report")
    if not report_dict:
        logger.error("[jira] Missing log_report in state")
        return {"errors": state.get("errors", []) + ["Missing log_report from classify step"], "jira_ticket": None, "finished": True}
    report = LogReport(**report_dict)
    plan_dict = state.get("remediation_plan")

    plan = None
    if plan_dict and plan_dict.get("incident_type") and plan_dict.get("severity"):
        from agents.remediation import RemediationPlan, RemediationStep
        plan = RemediationPlan(**{k: v for k, v in plan_dict.items() if k in RemediationPlan.__dataclass_fields__})
        plan.steps = [RemediationStep(**s) for s in plan_dict.get("steps", [])]

    try:
        ticket = agent.run(report, plan=plan, cookbook_md=state.get("cookbook_md", ""))
        return {
            "jira_ticket": ticket,
            "current_step": "jira",
            "completed_steps": state.get("completed_steps", []) + ["jira"],
            "finished": True,
        }
    except Exception as exc:
        logger.error("[jira] Error: %s", exc)
        return {"errors": state.get("errors", []) + [str(exc)], "jira_ticket": None, "finished": True}


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """
    Assemble and compile the LangGraph :class:`StateGraph`.

    The pipeline is a linear chain of five nodes:
    ``classify → remediate → cookbook → notify → jira → END``.

    Each node may set ``finished = True`` on error to short-circuit the
    remaining nodes.

    Returns
    -------
    StateGraph
        A compiled, runnable LangGraph instance.
    """
    graph = StateGraph(IncidentState)

    graph.add_node("classify", classify_node)
    graph.add_node("remediate", remediate_node)
    graph.add_node("cookbook", cookbook_node)
    graph.add_node("notify", notify_node)
    graph.add_node("jira", jira_node)

    graph.set_entry_point("classify")
    graph.add_edge("classify", "remediate")
    graph.add_edge("remediate", "cookbook")
    graph.add_edge("cookbook", "notify")
    graph.add_edge("notify", "jira")
    graph.add_edge("jira", END)

    return graph.compile()
