from __future__ import annotations

from ai_app.agents.base import AgentBase
from ai_app.schemas.research import FollowUpQuestion, ResearchSession


class HypothesisAgent(AgentBase):
    name = "hypothesis_agent"

    async def run(self, session: ResearchSession) -> list[FollowUpQuestion]:
        base = session.query.rstrip("?")
        return [
            FollowUpQuestion(question=f"What new evidence would strengthen the answer to: {base}?", rationale="Identify stronger validation paths."),
            FollowUpQuestion(question=f"Which claims about {base} remain contested?", rationale="Focus on disagreements."),
            FollowUpQuestion(question=f"What should be monitored next about {base}?", rationale="Track emerging changes."),
        ]

