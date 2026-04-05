from __future__ import annotations

from incident_suite.agents.common import with_stage
from incident_suite.models.schemas import EvidenceItem
from incident_suite.models.state import IncidentState


def verifier_node(state: IncidentState) -> IncidentState:
    verified_items = []
    for item in state.get("evidence_items", []):
        verified = item.verified or any("CRITICAL" in evidence.upper() for evidence in item.supporting_evidence)
        confidence = max(item.confidence, 0.86 if verified else item.confidence)
        verified_items.append(
            EvidenceItem(
                claim=item.claim,
                supporting_evidence=item.supporting_evidence,
                verified=verified,
                confidence=confidence,
                source_doc_ids=item.source_doc_ids,
            )
        )
    return with_stage(state, "verifier", "completed", "Fact verification raised confidence on evidence backed by repeated or explicit failure signals.", evidence_items=verified_items, status="verified")
