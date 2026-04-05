"""Runner – public entry-point that invokes the LangGraph pipeline."""

from __future__ import annotations

import logging
import uuid
from typing import Callable, Optional

from orchestrator.graph import build_graph
from orchestrator.state import IncidentState

logger = logging.getLogger(__name__)

_graph = None  # module-level singleton


def _get_graph():
    """Return the module-level compiled graph singleton, building it on first call."""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_incident_pipeline(
    raw_log: str,
    filename: str = "unknown.log",
    run_id: Optional[str] = None,
    on_step_update: Optional[Callable[[IncidentState], None]] = None,
) -> IncidentState:
    """
    Execute the full incident-analysis pipeline.

    Uses ``graph.stream()`` so that *on_step_update* is called with the merged
    state after every node completes, enabling live progress updates.

    Parameters
    ----------
    raw_log:
        The raw log text to analyse.
    filename:
        Original filename (for display / JIRA attachment purposes).
    run_id:
        Optional idempotency key; a UUID is generated when omitted.
    on_step_update:
        Optional callback invoked with the current merged state after each
        node finishes.  Use this to push incremental progress to a store.

    Returns
    -------
    IncidentState
        The final merged state after all agents have run.
    """
    run_id = run_id or str(uuid.uuid4())
    logger.info("Starting incident pipeline run_id=%s file=%s", run_id, filename)

    initial_state: IncidentState = {
        "run_id": run_id,
        "raw_log": raw_log,
        "filename": filename,
        "log_report": None,
        "remediation_plan": None,
        "cookbook_md": None,
        "slack_sent": None,
        "jira_ticket": None,
        "current_step": "init",
        "completed_steps": [],
        "errors": [],
        "finished": False,
    }

    graph = _get_graph()

    # Stream node-by-node so callers can receive live progress updates.
    # Each chunk is {node_name: partial_state_dict}; we merge into running state.
    running: IncidentState = dict(initial_state)  # type: ignore[assignment]
    for chunk in graph.stream(initial_state):
        for node_output in chunk.values():
            running.update(node_output)
        if on_step_update is not None:
            on_step_update(dict(running))  # type: ignore[arg-type]

    logger.info("Pipeline finished run_id=%s errors=%s", run_id, running.get("errors"))
    return running
