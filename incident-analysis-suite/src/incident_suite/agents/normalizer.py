from __future__ import annotations

from incident_suite.agents.common import with_stage
from incident_suite.models.schemas import DetectedIssue, ParsedEvent
from incident_suite.models.state import IncidentState


def infer_apex_class_name(raw_logs: str) -> str:
    lines = raw_logs.splitlines()
    for line in lines:
        if "METHOD_ENTRY" in line and "|" in line:
            candidate = line.split("|")[-1].split("(")[0].strip()
            if "." in candidate:
                class_name = candidate.split(".")[0].strip()
                if class_name:
                    return class_name
    for line in lines:
        if "CODE_UNIT_STARTED" in line and " trigger event" in line:
            tail = line.split("|")[-1].strip()
            candidate = tail.split(" on ")[0].strip()
            if candidate:
                return candidate
    return ""


def build_issue_candidate(raw_logs: str, parsed_events: list[ParsedEvent], salesforce_class_name: str, salesforce_class_body: str) -> DetectedIssue | None:
    if not parsed_events:
        return None

    upper_logs = raw_logs.upper()
    top_event = parsed_events[0]
    inferred_class = salesforce_class_name or infer_apex_class_name(raw_logs)
    soql_count = upper_logs.count("SOQL_EXECUTE_BEGIN")

    if inferred_class and soql_count >= 5:
        return DetectedIssue(
            title=f"Potential SOQL-in-loop governor limit risk in {inferred_class}",
            category="salesforce_governor_limits",
            severity="high" if soql_count >= 20 else "medium",
            probable_root_cause=(
                f"The Apex trace shows {soql_count} SOQL executions around {inferred_class}, which suggests query work may be happening inside iterative trigger or handler logic."
            ),
            evidence=[event.message or "" for event in parsed_events[:5]],
            impacted_services=["salesforce", inferred_class],
            confidence=0.88 if soql_count >= 20 else 0.8,
        )

    if inferred_class and "TRIGGER" in upper_logs:
        return DetectedIssue(
            title=f"Trigger bulkification risk in {inferred_class}",
            category="salesforce_trigger_design",
            severity=top_event.severity or "medium",
            probable_root_cause="The uploaded Apex trace points to trigger-driven execution that should be reviewed for bulk-safe query and DML patterns.",
            evidence=[event.message or "" for event in parsed_events[:5]],
            impacted_services=["salesforce", inferred_class],
            confidence=0.77,
        )

    if salesforce_class_body.strip():
        target_name = salesforce_class_name or "Salesforce Apex class"
        return DetectedIssue(
            title=f"Integration instability in {target_name}",
            category="salesforce_integration",
            severity=top_event.severity or "medium",
            probable_root_cause="The incident appears tied to Salesforce-backed execution and should be reviewed against the fetched Apex implementation.",
            evidence=[event.message or "" for event in parsed_events[:4]],
            impacted_services=["salesforce", target_name],
            confidence=0.72,
        )

    return DetectedIssue(
        title=f"{top_event.service or 'Service'} instability detected",
        category="integration" if salesforce_class_body else "availability",
        severity=top_event.severity or "medium",
        probable_root_cause="Repeated timeouts or failures observed in the uploaded evidence.",
        evidence=[event.message or "" for event in parsed_events[:3]],
        impacted_services=[event.service or "unknown-service" for event in parsed_events[:3]],
        confidence=0.78,
    )


def normalizer_node(state: IncidentState) -> IncidentState:
    raw_logs = state.get("raw_logs", "")
    lines = [line.strip() for line in raw_logs.splitlines() if line.strip()]
    parsed_events = []
    for line in lines[:20]:
        upper = line.upper()
        severity = "critical" if "CRITICAL" in upper else "high" if "ERROR" in upper else "medium"
        service = "salesforce" if "SALESFORCE" in upper else "payments-api" if "PAYMENTS" in upper else "unknown-service"
        parsed_events.append(ParsedEvent(severity=severity, service=service, message=line, signature=line.split()[-1] if line.split() else None))

    issue = build_issue_candidate(
        raw_logs=raw_logs,
        parsed_events=parsed_events,
        salesforce_class_name=state.get("salesforce_class_name", ""),
        salesforce_class_body=state.get("salesforce_class_body", ""),
    )
    issues = [issue] if issue else []
    return with_stage(state, "normalizer", "completed", "Source normalization parsed raw logs into normalized events and issue candidates.", parsed_events=parsed_events, detected_issues=issues, status="normalized")
