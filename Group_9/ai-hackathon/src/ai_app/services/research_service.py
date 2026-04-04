from __future__ import annotations

from ai_app.memory.session_store import SessionStore
from ai_app.schemas.research import ResearchSession


class ResearchService:
    def __init__(self, session_store: SessionStore) -> None:
        self.session_store = session_store

    def create_session(self, session: ResearchSession) -> ResearchSession:
        return self.session_store.create(session)

    def save(self, session: ResearchSession) -> ResearchSession:
        return self.session_store.save(session)
