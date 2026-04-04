from __future__ import annotations

from typing import TypedDict

from ai_app.schemas.research import ResearchSession


class GraphState(TypedDict):
    session: ResearchSession

