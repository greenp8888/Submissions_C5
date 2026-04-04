from __future__ import annotations

import asyncio
from collections import defaultdict

from ai_app.schemas.research import AgentTraceEntry, ResearchEvent, ResearchSession


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, ResearchSession] = {}
        self._queues: dict[str, asyncio.Queue[ResearchEvent]] = defaultdict(asyncio.Queue)

    def create(self, session: ResearchSession) -> ResearchSession:
        self._sessions[session.session_id] = session
        self._queues.setdefault(session.session_id, asyncio.Queue())
        return session

    def get(self, session_id: str) -> ResearchSession:
        return self._sessions[session_id]

    def save(self, session: ResearchSession) -> ResearchSession:
        self._sessions[session.session_id] = session
        return session

    def queue(self, session_id: str) -> asyncio.Queue[ResearchEvent]:
        return self._queues[session_id]

    async def emit(self, session_id: str, event: ResearchEvent) -> None:
        session = self._sessions[session_id]
        session.events.append(event)
        await self._queues[session_id].put(event)

    def trace(self, session_id: str, trace: AgentTraceEntry) -> None:
        session = self._sessions[session_id]
        session.agent_trace.append(trace)

