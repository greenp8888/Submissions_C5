from __future__ import annotations

from ai_app.agents.base import AgentBase
from ai_app.domain.enums import Depth
from ai_app.llms.client import OpenRouterClient
from ai_app.schemas.research import ResearchSession


class PlannerAgent(AgentBase):
    name = "planner_agent"

    def __init__(self, llm_client: OpenRouterClient) -> None:
        self.llm_client = llm_client

    async def run(self, session: ResearchSession) -> ResearchSession:
        if self.llm_client.enabled:
            prompt = (
                f"Break this research question into concise sub-questions.\n"
                f"Question: {session.query}\n"
                f"Depth: {session.depth.value}\n"
                "Return each sub-question on a new line."
            )
            completion = await self.llm_client.complete("You are a research planning agent.", prompt)
            parts = [line.lstrip("-0123456789. ").strip() for line in completion.splitlines() if line.strip()]
            if parts:
                session.sub_questions = parts[: self._max_questions(session.depth)]
                return session

        session.sub_questions = self._heuristic_questions(session.query, session.depth)
        return session

    def _max_questions(self, depth: Depth) -> int:
        if depth == Depth.QUICK:
            return 3
        if depth == Depth.STANDARD:
            return 6
        return 10

    def _heuristic_questions(self, query: str, depth: Depth) -> list[str]:
        base = [
            f"What are the core facts, definitions, and scope of: {query}?",
            f"What evidence or sources best support the current understanding of: {query}?",
            f"What are the major disagreements, controversies, or weak evidence areas for: {query}?",
        ]
        if depth != Depth.QUICK:
            base.extend(
                [
                    f"What recent news or changes affect: {query}?",
                    f"What academic or research-backed findings are relevant to: {query}?",
                ]
            )
        if depth == Depth.DEEP:
            base.extend(
                [
                    f"What emerging trends or future implications relate to: {query}?",
                    f"What follow-up questions remain unresolved about: {query}?",
                ]
            )
        return base[: self._max_questions(depth)]

