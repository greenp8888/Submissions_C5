from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
import threading
from collections import defaultdict
from datetime import timezone
from pathlib import Path

from ai_app.config import Settings
from ai_app.domain.enums import ResearchStatus
from ai_app.schemas.research import AgentTraceEntry, ResearchEvent, ResearchSession, utc_now


class SessionStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.db_path = settings.data_dir / "sessions.db"
        self._sessions: dict[str, ResearchSession] = {}
        self._queues: dict[str, asyncio.Queue[ResearchEvent]] = defaultdict(asyncio.Queue)
        self._lock = threading.Lock()
        self._ensure_schema()
        self._recover_running_sessions()

    def create(self, session: ResearchSession) -> ResearchSession:
        session.updated_at = utc_now()
        self._sessions[session.session_id] = session
        self._queues.setdefault(session.session_id, asyncio.Queue())
        self._persist(session)
        return session

    def get(self, session_id: str) -> ResearchSession:
        if session_id in self._sessions:
            return self._sessions[session_id]
        session = self._load(session_id)
        if session is None:
            raise KeyError(session_id)
        self._sessions[session.session_id] = session
        self._queues.setdefault(session.session_id, asyncio.Queue())
        return session

    def save(self, session: ResearchSession) -> ResearchSession:
        session.updated_at = utc_now()
        self._sessions[session.session_id] = session
        self._persist(session)
        return session

    def queue(self, session_id: str) -> asyncio.Queue[ResearchEvent]:
        self.get(session_id)
        return self._queues[session_id]

    async def emit(self, session_id: str, event: ResearchEvent) -> None:
        session = self.get(session_id)
        session.events.append(event)
        self.save(session)
        await self._queues[session_id].put(event)

    def trace(self, session_id: str, trace: AgentTraceEntry) -> None:
        session = self.get(session_id)
        session.agent_trace.append(trace)
        self.save(session)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    persisted_at TEXT NOT NULL,
                    payload_version TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def _persist(self, session: ResearchSession) -> None:
        payload = session.model_dump(mode="json")
        payload_json = json.dumps(payload)
        payload_version = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        persisted_at = utc_now()
        session.persisted_at = persisted_at
        session.payload_version = payload_version
        payload = session.model_dump(mode="json")
        payload_json = json.dumps(payload)
        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO sessions(session_id, status, updated_at, persisted_at, payload_version, payload_json)
                    VALUES(?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        status=excluded.status,
                        updated_at=excluded.updated_at,
                        persisted_at=excluded.persisted_at,
                        payload_version=excluded.payload_version,
                        payload_json=excluded.payload_json
                    """,
                    (
                        session.session_id,
                        session.status.value,
                        session.updated_at.isoformat(),
                        persisted_at.isoformat(),
                        payload_version,
                        payload_json,
                    ),
                )
                connection.commit()

    def _load(self, session_id: str) -> ResearchSession | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return ResearchSession.model_validate_json(row["payload_json"])

    def _recover_running_sessions(self) -> None:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT session_id, payload_json FROM sessions WHERE status = ?",
                (ResearchStatus.RUNNING.value,),
            ).fetchall()
        if not rows:
            return
        for row in rows:
            session = ResearchSession.model_validate_json(row["payload_json"])
            session.status = ResearchStatus.ERROR
            session.updated_at = utc_now()
            session.metadata["error"] = "Server restarted while research was running."
            session.metadata["recovered_from_persistence"] = True
            session.events.append(
                ResearchEvent(
                    event_type="error",
                    agent="session_store",
                    message="Session restored from SQLite after a server restart. The active run did not resume automatically.",
                )
            )
            self._sessions[session.session_id] = session
            self._persist(session)
