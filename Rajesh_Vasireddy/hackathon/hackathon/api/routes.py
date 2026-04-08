"""API route definitions."""

from __future__ import annotations

import logging
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException

from api.schemas import AnalyzeRequest, RunResult
from orchestrator.runner import run_incident_pipeline
from orchestrator.state import IncidentState

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory store for completed runs (replace with Redis/DB for production)
_run_store: Dict[str, IncidentState] = {}


# ---------------------------------------------------------------------------
# POST /analyze
# ---------------------------------------------------------------------------

@router.post("/analyze", response_model=RunResult, status_code=202)
async def analyze_log(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Submit a log file for analysis.
    The pipeline runs in the background; poll GET /status/{run_id} for results.
    """
    import uuid
    run_id = request.run_id or str(uuid.uuid4())

    if run_id in _run_store:
        raise HTTPException(status_code=409, detail=f"run_id '{run_id}' already exists.")

    # Placeholder so callers can poll immediately
    _run_store[run_id] = {  # type: ignore[assignment]
        "run_id": run_id,
        "filename": request.filename,
        "finished": False,
        "current_step": "queued",
        "completed_steps": [],
        "errors": [],
    }

    background_tasks.add_task(_run_pipeline, run_id, request.content, request.filename)

    return _to_run_result(_run_store[run_id])


def _run_pipeline(run_id: str, raw_log: str, filename: str) -> None:
    """Background task: stream the pipeline and update ``_run_store`` after every node."""
    def _on_step(state: IncidentState) -> None:
        _run_store[run_id] = state

    try:
        final_state = run_incident_pipeline(
            raw_log=raw_log,
            filename=filename,
            run_id=run_id,
            on_step_update=_on_step,
        )
        _run_store[run_id] = final_state
    except Exception as exc:
        logger.exception("Pipeline error for run_id=%s", run_id)
        _run_store[run_id]["errors"] = [str(exc)]  # type: ignore[index]
        _run_store[run_id]["finished"] = True  # type: ignore[index]


# ---------------------------------------------------------------------------
# GET /runs  (list all run IDs with summary)
# ---------------------------------------------------------------------------

@router.get("/runs")
async def list_runs():
    """Return a summary list of all submitted runs."""
    runs = []
    for run_id, state in _run_store.items():
        report = state.get("log_report") or {}
        runs.append({
            "run_id": run_id,
            "filename": state.get("filename", ""),
            "finished": state.get("finished", False),
            "severity": report.get("severity"),
            "incident_type": report.get("incident_type"),
            "current_step": state.get("current_step", ""),
        })
    return {"runs": runs}


# ---------------------------------------------------------------------------
# GET /status/{run_id}
# ---------------------------------------------------------------------------

@router.get("/status/{run_id}", response_model=RunResult)
async def get_status(run_id: str):
    """Poll the status and results of a previously submitted analysis."""
    state = _run_store.get(run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"run_id '{run_id}' not found.")
    return _to_run_result(state)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _to_run_result(state: IncidentState) -> RunResult:
    """Map an :class:`~orchestrator.state.IncidentState` dict to a :class:`~api.schemas.RunResult` response model."""
    report = state.get("log_report") or {}
    return RunResult(
        run_id=state.get("run_id", ""),
        filename=state.get("filename", ""),
        finished=state.get("finished", False),
        current_step=state.get("current_step", ""),
        completed_steps=state.get("completed_steps", []),
        errors=state.get("errors", []),
        severity=report.get("severity"),
        incident_type=report.get("incident_type"),
        root_cause=report.get("root_cause"),
        affected_services=report.get("affected_services", []),
        raw_summary=report.get("raw_summary"),
        cookbook_md=state.get("cookbook_md"),
        slack_sent=state.get("slack_sent"),
        jira_ticket=state.get("jira_ticket"),
        log_report=report or None,
        remediation_plan=state.get("remediation_plan"),
    )
