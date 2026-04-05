from __future__ import annotations

from incident_suite.agents.common import with_stage
from incident_suite.models.state import IncidentState


def qa_node(state: IncidentState) -> IncidentState:
    qa_passed = bool(state.get("detected_issues")) and bool(state.get("code_fixes")) and bool(state.get("report_markdown"))
    message = "QA passed: report, fixes, and findings are present." if qa_passed else "QA requested self-correction because one or more outputs are incomplete."
    return with_stage(state, "qa", "completed", message, qa_passed=qa_passed, status="qa_complete")
