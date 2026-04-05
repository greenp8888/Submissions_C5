from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ParsedEvent(BaseModel):
    timestamp: str | None = None
    service: str | None = None
    environment: str | None = None
    severity: str | None = None
    signature: str | None = None
    message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceDocument(BaseModel):
    doc_id: str
    title: str
    source_type: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    chunk_id: str
    content: str
    source_type: str
    score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class DetectedIssue(BaseModel):
    title: str
    category: str
    severity: str
    probable_root_cause: str
    evidence: list[str] = Field(default_factory=list)
    impacted_services: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class EvidenceItem(BaseModel):
    claim: str
    supporting_evidence: list[str] = Field(default_factory=list)
    verified: bool = False
    confidence: float = 0.0
    source_doc_ids: list[str] = Field(default_factory=list)


class InsightItem(BaseModel):
    title: str
    detail: str
    severity: str
    rationale: str


class RemediationPlan(BaseModel):
    issue_title: str
    fix: str
    rationale: str
    urgency: str
    validation_steps: list[str] = Field(default_factory=list)
    rollback_steps: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class CodeFixSuggestion(BaseModel):
    issue_title: str
    recommended_change: str
    analogy: str
    target_component: str
    suggested_code: str
    validation_notes: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class CookbookOutput(BaseModel):
    title: str
    summary: str
    checklist: list[str] = Field(default_factory=list)
    escalation_rules: list[str] = Field(default_factory=list)
    prevention_steps: list[str] = Field(default_factory=list)


class StageEvent(BaseModel):
    stage: str
    status: str
    message: str


class ExportArtifact(BaseModel):
    name: str
    kind: str
    content: str


class ExternalActionResult(BaseModel):
    success: bool = False
    external_id: str | None = None
    url: str | None = None
    message: str | None = None


class AnalyzeIncidentRequest(BaseModel):
    source: str = "streamlit"
    query: str = "Analyze the uploaded logs and propose a fix."
    raw_logs: str
    salesforce_class_name: str | None = None
    salesforce_class_body: str | None = None
    severity_override: str | None = None
    runtime_salesforce_instance_url: str | None = None
    runtime_salesforce_access_token: str | None = None
    runtime_slack_bot_token: str | None = None
    runtime_slack_channel_id: str | None = None
    runtime_jira_base_url: str | None = None
    runtime_jira_email: str | None = None
    runtime_jira_api_token: str | None = None
    runtime_jira_project_key: str | None = None
    openrouter_api_key: str | None = None
    openrouter_model: str | None = None


class AnalyzeIncidentResponse(BaseModel):
    incident_id: str
    severity: str
    plan: list[str] = Field(default_factory=list)
    sub_queries: list[str] = Field(default_factory=list)
    source_documents: list[SourceDocument] = Field(default_factory=list)
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    parsed_events: list[ParsedEvent] = Field(default_factory=list)
    detected_issues: list[DetectedIssue] = Field(default_factory=list)
    evidence_items: list[EvidenceItem] = Field(default_factory=list)
    insights: list[InsightItem] = Field(default_factory=list)
    remediations: list[RemediationPlan] = Field(default_factory=list)
    code_fixes: list[CodeFixSuggestion] = Field(default_factory=list)
    cookbook: CookbookOutput | None = None
    report_markdown: str = ""
    mermaid_diagram: str = ""
    export_artifacts: list[ExportArtifact] = Field(default_factory=list)
    stage_events: list[StageEvent] = Field(default_factory=list)
    slack_result: ExternalActionResult | None = None
    salesforce_result: ExternalActionResult | None = None
    jira_result: ExternalActionResult | None = None
    status: str
