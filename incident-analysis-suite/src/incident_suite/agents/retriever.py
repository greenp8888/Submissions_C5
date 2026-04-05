from __future__ import annotations

from incident_suite.agents.common import with_stage
from incident_suite.models.state import IncidentState
from incident_suite.tools.vector_store import IncidentVectorStore, default_vector_store_path


def retriever_node(state: IncidentState) -> IncidentState:
    incident_id = state.get("incident_id", "incident")
    query = " ".join(state.get("sub_queries", [])) or state.get("query", "")
    store = IncidentVectorStore(default_vector_store_path())
    retrieved = store.search(incident_id, query, limit=6)
    return with_stage(
        state,
        "retriever",
        "completed",
        f"Contextual retriever returned {len(retrieved)} chunk(s) for evidence review.",
        retrieved_chunks=retrieved,
        status="retrieved",
    )
