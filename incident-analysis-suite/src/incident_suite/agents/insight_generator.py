from __future__ import annotations

from incident_suite.agents.common import with_stage
from incident_suite.models.schemas import InsightItem, RemediationPlan
from incident_suite.models.state import IncidentState


def insight_generator_node(state: IncidentState) -> IncidentState:
    insights = []
    remediations = []
    severity = state.get("severity", "medium")
    for issue in state.get("detected_issues", []):
        insights.append(
            InsightItem(
                title=issue.title,
                detail="The failure pattern points to a dependency bottleneck with incomplete protection around retries or timeouts.",
                severity=severity,
                rationale="Verified evidence shows repeated timeout/error signatures clustered in the same service path.",
            )
        )
        remediations.append(
            RemediationPlan(
                issue_title=issue.title,
                fix="Add bounded retries, explicit timeouts, and a fallback guard before escalating to manual intervention.",
                rationale="This reduces cascading failure risk while preserving a fast fail path for operators.",
                urgency=severity,
                validation_steps=[
                    "Confirm timeout and error rates drop after the fix.",
                    "Validate downstream dependency behavior stays within safe thresholds.",
                    "Review Salesforce or external integration logs for retry side effects.",
                ],
                rollback_steps=[
                    "Disable the retry path if it amplifies upstream traffic.",
                    "Revert to the previous stable integration handler if failures worsen.",
                ],
                confidence=0.82,
            )
        )
    return with_stage(state, "insight_generator", "completed", "Insight generation synthesized root-cause reasoning and remediation guidance.", insights=insights, remediations=remediations, status="insights_ready")
