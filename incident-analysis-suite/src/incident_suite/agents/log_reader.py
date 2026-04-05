from incident_suite.models.schemas import DetectedIssue, ParsedEvent
from incident_suite.models.state import IncidentState


def log_reader_classifier_node(state: IncidentState) -> IncidentState:
    raw_logs = state.get("raw_logs", "")
    parsed = [
        ParsedEvent(
            severity="critical" if "CRITICAL" in raw_logs.upper() else "high" if "ERROR" in raw_logs.upper() else "medium",
            message=raw_logs[:500],
        )
    ]
    issues = [
        DetectedIssue(
            title="Service instability detected",
            category="availability",
            severity=parsed[0].severity or "medium",
            probable_root_cause="Repeated error patterns detected in uploaded logs.",
            evidence=[raw_logs[:250]],
            impacted_services=["unknown-service"],
            confidence=0.74,
        )
    ]
    return {**state, "parsed_events": parsed, "detected_issues": issues, "status": "issues_detected"}
