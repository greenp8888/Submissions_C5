from incident_suite.agents.common import with_stage
from incident_suite.models.schemas import ExternalActionResult
from incident_suite.models.state import IncidentState
from incident_suite.tools.jira import create_issue


def jira_ticket_node(state: IncidentState) -> IncidentState:
    if not state.get("requires_jira"):
        return with_stage(
            state,
            "jira_ticket_agent",
            "completed",
            "Jira ticket agent skipped ticket creation because the incident did not require escalation.",
            jira_result=ExternalActionResult(success=False, message="Jira creation skipped."),
            status="complete",
        )

    issues = state.get("detected_issues", [])
    remediations = state.get("remediations", [])
    summary = f"[{state.get('severity', 'medium').upper()}] {issues[0].title if issues else 'Incident follow-up'}"
    description = remediations[0].fix if remediations else "Manual investigation required."
    jira_result = create_issue(
        summary=summary,
        description=description,
        priority=state.get("severity", "medium"),
        base_url=state.get("runtime_jira_base_url"),
        email=state.get("runtime_jira_email"),
        api_token=state.get("runtime_jira_api_token"),
        project_key=state.get("runtime_jira_project_key"),
    )
    return with_stage(
        state,
        "jira_ticket_agent",
        "completed",
        "Jira ticket created." if jira_result.success else f"Jira ticket skipped or failed: {jira_result.message}",
        jira_result=jira_result,
        status="complete",
    )
