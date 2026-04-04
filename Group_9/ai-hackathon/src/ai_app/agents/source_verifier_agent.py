from __future__ import annotations

from ai_app.agents.base import AgentBase
from ai_app.retrieval.source_scoring import credibility_for_source
from ai_app.schemas.research import ResearchSession


class SourceVerifierAgent(AgentBase):
    name = "source_verifier_agent"

    async def run(self, session: ResearchSession) -> ResearchSession:
        for source in session.sources:
            source.credibility_score = credibility_for_source(source)
        return session

