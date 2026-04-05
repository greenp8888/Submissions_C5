from uuid import uuid4

from incident_suite.agents.common import with_stage
from incident_suite.models.state import IncidentState


def orchestrator_node(state: IncidentState) -> IncidentState:
    raw_logs = state.get("raw_logs", "")
    severity_override = state.get("severity_override", "").lower()
    upper_logs = raw_logs.upper()
    soql_count = upper_logs.count("SOQL_EXECUTE_BEGIN")
    severity_reason = "No strong severity signal was found, so the incident stayed at medium."
    if severity_override:
        severity = severity_override
        severity_reason = f"Severity override was provided in the UI as {severity_override}."
    elif "CRITICAL" in upper_logs:
        severity = "critical"
        severity_reason = "The uploaded logs contain explicit CRITICAL markers."
    elif "ERROR" in upper_logs:
        severity = "high"
        severity_reason = "The uploaded logs contain explicit ERROR markers."
    elif soql_count >= 20:
        severity = "high"
        severity_reason = (
            f"The Apex trace shows {soql_count} SOQL executions in a tight path, which strongly suggests a governor-limit or looped-query issue."
        )
    else:
        severity = "medium"
    return with_stage(
        state,
        "orchestrator",
        "completed",
        f"Orchestrator initialized incident routing with severity {severity}. Reason: {severity_reason}",
        incident_id=state.get("incident_id", f"inc-{uuid4().hex[:12]}"),
        severity=severity,
        requires_jira=severity in {"high", "critical"},
        status="classified",
    )
