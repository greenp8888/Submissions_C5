"""Pydantic request/response schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Request body for ``POST /analyze``."""

    filename: str = Field(default="upload.log", description="Original log filename")
    content: str = Field(..., description="Raw log text (UTF-8)")
    run_id: Optional[str] = Field(default=None, description="Optional idempotency key")


class RunResult(BaseModel):
    """
    Full result payload returned by ``GET /status/{run_id}`` and ``POST /analyze``.

    Fields are ``None`` until the corresponding pipeline stage completes.
    """

    run_id: str
    filename: str
    finished: bool
    current_step: str
    completed_steps: List[str]
    errors: List[str]
    severity: Optional[str] = None
    incident_type: Optional[str] = None
    root_cause: Optional[str] = None
    affected_services: List[str] = []
    raw_summary: Optional[str] = None
    cookbook_md: Optional[str] = None
    slack_sent: Optional[bool] = None
    jira_ticket: Optional[str] = None
    log_report: Optional[Dict[str, Any]] = None
    remediation_plan: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Response body for ``GET /healthz`` liveness probe."""

    status: str = "ok"
    version: str = "1.0.0"
