from incident_suite.agents.common import with_stage
from incident_suite.models.schemas import CookbookOutput
from incident_suite.models.state import IncidentState


def cookbook_node(state: IncidentState) -> IncidentState:
    issues = state.get("detected_issues", [])
    title = f"Cookbook for {issues[0].title}" if issues else "Incident Cookbook"
    cookbook = CookbookOutput(
        title=title,
        summary="A reusable runbook derived from the current incident.",
        checklist=[
            "Validate alert scope and impacted services.",
            "Contain the incident before applying permanent changes.",
            "Execute remediation and verify service recovery.",
            "Document root cause and prevention tasks.",
        ],
        escalation_rules=[
            "Escalate immediately if customer-facing APIs are degraded.",
            "Page platform owner if remediation confidence is below 0.7.",
        ],
        prevention_steps=[
            "Add log-based alerts for the detected signature.",
            "Create post-incident follow-up for durable mitigation.",
        ],
    )
    return with_stage(
        state,
        "cookbook_synthesizer",
        "completed",
        "Cookbook synthesizer turned the incident into a reusable runbook checklist.",
        cookbook=cookbook,
        status="cookbook_ready",
    )
