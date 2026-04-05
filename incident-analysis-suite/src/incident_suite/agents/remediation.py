from incident_suite.models.schemas import RemediationPlan
from incident_suite.models.state import IncidentState


def remediation_node(state: IncidentState) -> IncidentState:
    issues = state.get("detected_issues", [])
    remediations = [
        RemediationPlan(
            issue_title=issue.title,
            fix="Restart the impacted service, validate dependency health, and roll forward only after error rate normalizes.",
            rationale="The log pattern suggests an active service-side failure that should be contained before broader impact spreads.",
            urgency=issue.severity,
            validation_steps=[
                "Confirm error rate drops below threshold.",
                "Verify downstream service connectivity.",
                "Check customer-facing latency and availability dashboards.",
            ],
            rollback_steps=[
                "Rollback the latest deployment if a recent release correlates with the incident.",
                "Revert configuration changes affecting the failing service.",
            ],
            confidence=0.8,
        )
        for issue in issues
    ]
    return {**state, "remediations": remediations, "status": "remediated"}
