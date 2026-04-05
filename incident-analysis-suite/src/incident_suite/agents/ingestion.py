from __future__ import annotations

from incident_suite.agents.common import with_stage
from incident_suite.models.schemas import SourceDocument
from incident_suite.models.state import IncidentState
from incident_suite.tools.vector_store import IncidentVectorStore, default_vector_store_path


def ingestion_node(state: IncidentState) -> IncidentState:
    incident_id = state.get("incident_id", "incident")
    documents = [
        SourceDocument(
            doc_id=f"{incident_id}-logs",
            title="Uploaded incident logs",
            source_type="log",
            content=state.get("raw_logs", ""),
            metadata={"incident_id": incident_id},
        )
    ]
    if state.get("salesforce_class_body"):
        documents.append(
            SourceDocument(
                doc_id=f"{incident_id}-salesforce-class",
                title=state.get("salesforce_class_name", "Salesforce Apex Class"),
                source_type="salesforce_apex",
                content=state.get("salesforce_class_body", ""),
                metadata={"class_name": state.get("salesforce_class_name", "")},
            )
        )

    store = IncidentVectorStore(default_vector_store_path())
    ingested_chunks = store.ingest(incident_id, documents)
    return with_stage(
        state,
        "ingestion",
        "completed",
        f"Document ingestion stored {len(documents)} source document(s) and {len(ingested_chunks)} chunk(s) in LanceDB.",
        source_documents=documents,
        status="ingested",
    )
