from __future__ import annotations

from incident_suite.agents.common import with_stage
from incident_suite.models.state import IncidentState


def critical_analysis_node(state: IncidentState) -> IncidentState:
    override = state.get("severity_override", "").lower()
    issue_severities = [issue.severity for issue in state.get("detected_issues", [])]
    if override:
        severity = override
    elif "critical" in issue_severities:
        severity = "critical"
    elif "high" in issue_severities:
        severity = "high"
    else:
        severity = "medium"
    requires_jira = severity in {"high", "critical"}
    return with_stage(state, "critical_analysis", "completed", f"Critical analysis classified the incident as {severity}.", severity=severity, requires_jira=requires_jira, status="classified")
