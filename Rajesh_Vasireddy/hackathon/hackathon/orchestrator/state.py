"""IncidentState – the shared state dict passed through the LangGraph."""

from __future__ import annotations

from typing import List, Optional, TypedDict


class IncidentState(TypedDict, total=False):
    """
    Shared mutable state passed between every node in the LangGraph pipeline.

    All fields are optional (``total=False``) so that each graph node can
    return a *partial* dict and LangGraph will merge it into the running state.

    Input fields are populated once at pipeline start.  Agent-output fields are
    written by their respective nodes.  Pipeline-metadata fields are updated by
    every node to track progress and surface errors to the API layer.
    """
    # Input
    run_id: str
    raw_log: str
    filename: str

    # Agent outputs
    log_report: Optional[dict]          # serialised LogReport
    remediation_plan: Optional[dict]    # serialised RemediationPlan
    cookbook_md: Optional[str]
    slack_sent: Optional[bool]
    jira_ticket: Optional[str]

    # Pipeline metadata
    current_step: str
    completed_steps: List[str]
    errors: List[str]
    finished: bool
