from __future__ import annotations

from incident_suite.agents.common import with_stage
from incident_suite.models.schemas import EvidenceItem
from incident_suite.models.state import IncidentState


def evidence_node(state: IncidentState) -> IncidentState:
    issues = state.get("detected_issues", [])
    chunks = state.get("retrieved_chunks", [])
    evidence_items = []
    for issue in issues:
        supporting = [chunk.content[:240] for chunk in chunks[:3]] or issue.evidence
        evidence_items.append(
            EvidenceItem(
                claim=issue.title,
                supporting_evidence=supporting,
                verified=len(supporting) >= 2,
                confidence=0.72 if len(supporting) >= 2 else 0.51,
                source_doc_ids=[chunk.chunk_id for chunk in chunks[:3]],
            )
        )
    return with_stage(state, "evidence", "completed", "Evidence extraction assembled support for the key issue claims.", evidence_items=evidence_items, status="evidence_ready")
