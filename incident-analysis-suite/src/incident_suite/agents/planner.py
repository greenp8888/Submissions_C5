from __future__ import annotations

from incident_suite.agents.common import with_stage
from incident_suite.models.state import IncidentState


def planner_node(state: IncidentState) -> IncidentState:
    query = state.get("query", "Analyze the uploaded logs and propose a fix.")
    plan = [
        "Decompose the request into retrieval and verification tasks.",
        "Ingest logs and available source code into LanceDB.",
        "Extract evidence, verify severity, and generate fixes plus a report.",
    ]
    return with_stage(state, "planner", "completed", f"Planner created a response plan for: {query}", plan=plan, status="planned")
