from __future__ import annotations

from uuid import uuid4

from incident_suite.graph.workflow import build_workflow
from incident_suite.models.schemas import AnalyzeIncidentRequest, AnalyzeIncidentResponse


def build_initial_state(request: AnalyzeIncidentRequest) -> dict:
    return {
        "incident_id": f"inc-{uuid4().hex[:12]}",
        "source": request.source,
        "query": request.query,
        "raw_logs": request.raw_logs,
        "salesforce_class_name": request.salesforce_class_name or "",
        "salesforce_class_body": request.salesforce_class_body or "",
        "severity_override": request.severity_override or "",
        "runtime_salesforce_instance_url": request.runtime_salesforce_instance_url or "",
        "runtime_salesforce_access_token": request.runtime_salesforce_access_token or "",
        "runtime_slack_bot_token": request.runtime_slack_bot_token or "",
        "runtime_slack_channel_id": request.runtime_slack_channel_id or "",
        "runtime_jira_base_url": request.runtime_jira_base_url or "",
        "runtime_jira_email": request.runtime_jira_email or "",
        "runtime_jira_api_token": request.runtime_jira_api_token or "",
        "runtime_jira_project_key": request.runtime_jira_project_key or "",
        "openrouter_api_key": request.openrouter_api_key or "",
        "openrouter_model": request.openrouter_model or "",
        "stage_events": [],
    }


def analyze_incident(request: AnalyzeIncidentRequest) -> AnalyzeIncidentResponse:
    workflow = build_workflow()
    final_state = workflow.invoke(build_initial_state(request))
    return AnalyzeIncidentResponse(**final_state)


def stream_incident(request: AnalyzeIncidentRequest):
    workflow = build_workflow()
    return workflow.stream(build_initial_state(request), stream_mode="updates")
