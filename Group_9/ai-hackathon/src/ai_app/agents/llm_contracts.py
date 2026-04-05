from __future__ import annotations

from pydantic import BaseModel, Field


class PlannerOutput(BaseModel):
    sub_questions: list[str] = Field(default_factory=list)


class AnalysisClaimDraft(BaseModel):
    statement: str
    supporting_source_ids: list[str] = Field(default_factory=list)
    source_finding_ids: list[str] = Field(default_factory=list)
    confidence_pct: int = 50
    reasoning: str = ""
    credibility_summary: str = ""
    evidence_summary: str = ""
    contested: bool = False
    weak_evidence: bool = False
    debate_position: str = ""
    consensus_pct: int = 50


class AnalysisOutput(BaseModel):
    claims: list[AnalysisClaimDraft] = Field(default_factory=list)


class ContradictionDraft(BaseModel):
    claim_a_id: str
    claim_b_id: str
    analysis: str
    credibility_lean: str = "mixed"
    weighting_rationale: str = ""
    conflict_level: str = "mixed"
    consensus_pct: int = 50


class ContradictionOutput(BaseModel):
    contradictions: list[ContradictionDraft] = Field(default_factory=list)


class InsightDraft(BaseModel):
    label: str
    content: str
    insight_type: str = "trend"
    evidence_chain: list[str] = Field(default_factory=list)


class EntityDraft(BaseModel):
    name: str
    entity_type: str = "concept"
    description: str = ""
    source_ids: list[str] = Field(default_factory=list)


class RelationshipDraft(BaseModel):
    source_entity_name: str
    target_entity_name: str
    relationship_type: str
    description: str = ""


class FollowUpDraft(BaseModel):
    question: str
    rationale: str = ""


class InsightOutput(BaseModel):
    insights: list[InsightDraft] = Field(default_factory=list)
    entities: list[EntityDraft] = Field(default_factory=list)
    relationships: list[RelationshipDraft] = Field(default_factory=list)
    follow_up_questions: list[FollowUpDraft] = Field(default_factory=list)


class QAWarningDraft(BaseModel):
    severity: str = "medium"
    message: str
    related_claim_ids: list[str] = Field(default_factory=list)


class QAReviewOutput(BaseModel):
    verdict: str = "pass"
    summary: str = ""
    warnings: list[QAWarningDraft] = Field(default_factory=list)
