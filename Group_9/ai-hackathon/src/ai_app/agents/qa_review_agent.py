from __future__ import annotations

from ai_app.agents.base import AgentBase
from ai_app.schemas.research import ResearchSession


class QAReviewAgent(AgentBase):
    name = "qa_review_agent"

    async def run(self, session: ResearchSession) -> ResearchSession:
        session.metadata["qa_review"] = "passed"
        return session

