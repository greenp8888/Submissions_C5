from __future__ import annotations

from typing import TypedDict

from incident_suite.models.schemas import (
    CodeFixSuggestion,
    CookbookOutput,
    DetectedIssue,
    EvidenceItem,
    ExportArtifact,
    ExternalActionResult,
    InsightItem,
    ParsedEvent,
    RetrievedChunk,
    SourceDocument,
    StageEvent,
    RemediationPlan,
)


class IncidentState(TypedDict, total=False):
    incident_id: str
    source: str
    query: str
    raw_logs: str
    salesforce_class_name: str
    salesforce_class_body: str
    severity_override: str
    runtime_salesforce_instance_url: str
    runtime_salesforce_access_token: str
    runtime_slack_bot_token: str
    runtime_slack_channel_id: str
    runtime_jira_base_url: str
    runtime_jira_email: str
    runtime_jira_api_token: str
    runtime_jira_project_key: str
    openrouter_api_key: str
    openrouter_model: str
    plan: list[str]
    sub_queries: list[str]
    source_documents: list[SourceDocument]
    retrieved_chunks: list[RetrievedChunk]
    parsed_events: list[ParsedEvent]
    detected_issues: list[DetectedIssue]
    evidence_items: list[EvidenceItem]
    insights: list[InsightItem]
    remediations: list[RemediationPlan]
    code_fixes: list[CodeFixSuggestion]
    cookbook: CookbookOutput
    report_markdown: str
    mermaid_diagram: str
    export_artifacts: list[ExportArtifact]
    stage_events: list[StageEvent]
    slack_result: ExternalActionResult
    salesforce_result: ExternalActionResult
    jira_result: ExternalActionResult
    severity: str
    requires_jira: bool
    qa_passed: bool
    status: str
