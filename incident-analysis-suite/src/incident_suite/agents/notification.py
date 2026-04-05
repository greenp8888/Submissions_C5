from incident_suite.agents.common import with_stage
from incident_suite.models.state import IncidentState
from incident_suite.tools.salesforce import upsert_incident_case
from incident_suite.tools.slack import post_incident_message


def notification_node(state: IncidentState) -> IncidentState:
    issues = state.get("detected_issues", [])
    remediations = state.get("remediations", [])
    severity = state.get("severity", "medium")
    incident_id = state.get("incident_id", "unknown")

    top_issue = issues[0].title if issues else "Unknown incident"
    top_fix = remediations[0].fix if remediations else "No remediation generated."

    summary = (
        f"Incident {incident_id}\n"
        f"Severity: {severity}\n"
        f"Issue: {top_issue}\n"
        f"Recommended fix: {top_fix}"
    )

    slack_result = post_incident_message(
        summary,
        bot_token=state.get("runtime_slack_bot_token"),
        channel_id=state.get("runtime_slack_channel_id"),
    )
    salesforce_result = upsert_incident_case(
        subject=f"[{severity.upper()}] {top_issue}",
        description=summary,
        priority=severity,
        instance_url=state.get("runtime_salesforce_instance_url"),
        access_token=state.get("runtime_salesforce_access_token"),
    )
    notification_parts = []
    notification_parts.append(
        "Slack delivered." if slack_result.success else f"Slack skipped or failed: {slack_result.message}"
    )
    notification_parts.append(
        "Salesforce case synced." if salesforce_result.success else f"Salesforce sync skipped or failed: {salesforce_result.message}"
    )
    return with_stage(
        state,
        "notification_agent",
        "completed",
        " ".join(notification_parts),
        slack_result=slack_result,
        salesforce_result=salesforce_result,
        status="notified",
    )
