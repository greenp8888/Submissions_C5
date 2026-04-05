from __future__ import annotations

from incident_suite.agents.common import with_stage
from incident_suite.models.schemas import RemediationPlan
from incident_suite.models.state import IncidentState


def self_correct_node(state: IncidentState) -> IncidentState:
    remediations = list(state.get("remediations", []))
    if not remediations and state.get("detected_issues"):
        issue = state["detected_issues"][0]
        remediations.append(
            RemediationPlan(
                issue_title=issue.title,
                fix="Fallback recommendation: isolate the impacted integration path and apply a guarded retry strategy.",
                rationale="Self-correcting agent filled a missing remediation to keep the output actionable.",
                urgency=state.get("severity", "medium"),
                validation_steps=["Re-run analysis after applying the fallback change."],
                rollback_steps=["Remove the fallback mitigation if it introduces unintended side effects."],
                confidence=0.61,
            )
        )
    return with_stage(state, "self_correct", "completed", "Self-correcting agent repaired incomplete outputs before export.", remediations=remediations, status="self_corrected")
