from __future__ import annotations

from incident_suite.models.schemas import StageEvent
from incident_suite.models.state import IncidentState


def with_stage(state: IncidentState, stage: str, stage_status: str, message: str, **updates) -> IncidentState:
    stage_events = list(state.get("stage_events", []))
    stage_events.append(StageEvent(stage=stage, status=stage_status, message=message))
    return {**state, **updates, "stage_events": stage_events}
