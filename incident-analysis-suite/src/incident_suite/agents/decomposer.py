from __future__ import annotations

from incident_suite.agents.common import with_stage
from incident_suite.models.state import IncidentState


def decomposer_node(state: IncidentState) -> IncidentState:
    query = state.get("query", "")
    sub_queries = [
        "What are the highest-signal failures in the logs?",
        "What code path or integration is implicated?",
        "What evidence confirms the severity and recommended fix?",
        f"What answer best satisfies the user request: {query}",
    ]
    return with_stage(state, "decomposer", "completed", "Query decomposer expanded the user request into focused analysis tasks.", sub_queries=sub_queries, status="decomposed")
