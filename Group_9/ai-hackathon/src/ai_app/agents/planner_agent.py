from __future__ import annotations

from ai_app.agents.base import AgentBase
from ai_app.agents.llm_contracts import PlannerOutput
from ai_app.domain.enums import Depth
from ai_app.llms.client import OpenRouterClient
from ai_app.llms.prompts import load_prompt
from ai_app.llms.structured_output import parse_model
from ai_app.schemas.research import ResearchSession


class PlannerAgent(AgentBase):
    name = "planner_agent"

    def __init__(self, llm_client: OpenRouterClient) -> None:
        self.llm_client = llm_client
        self.system_prompt = load_prompt("system", "planner")

    async def run(self, session: ResearchSession) -> ResearchSession:
        if session.run_mode.value == "batch" and session.batch_topics:
            session.sub_questions = [topic for topic in session.batch_topics if topic][: self._max_questions(session.depth)]
            return session
        if session.debate_mode and session.position_a and session.position_b:
            planned = await self._plan_with_llm(
                session,
                (
                    "Generate balanced research sub-questions for a debate.\n"
                    f"Topic: {session.query}\n"
                    f"Position A: {session.position_a}\n"
                    f"Position B: {session.position_b}\n"
                    f"Depth: {session.depth.value}\n"
                    "Return JSON with key sub_questions. Prefix each item with [A], [B], or [SHARED]."
                ),
            )
            if planned:
                session.sub_questions = planned[: self._max_questions(session.depth)]
                return session
            session.sub_questions = self._heuristic_debate_questions(session.query, session.position_a, session.position_b, session.depth)
            return session
        planned = await self._plan_with_llm(
            session,
            (
                f"Break this research question into concise, non-overlapping sub-questions.\n"
                f"Question: {session.query}\n"
                f"Depth: {session.depth.value}\n"
                "Return JSON with key sub_questions."
            ),
        )
        if planned:
            session.sub_questions = planned[: self._max_questions(session.depth)]
            return session

        session.sub_questions = self._heuristic_questions(session.query, session.depth)
        return session

    async def _plan_with_llm(self, session: ResearchSession, prompt: str) -> list[str]:
        if not self.llm_client.enabled:
            return []
        payload = await self.llm_client.complete_json(self.system_prompt, prompt)
        parsed = parse_model(payload, PlannerOutput)
        if not parsed or not parsed.sub_questions:
            return []
        return [question.strip() for question in parsed.sub_questions if question and question.strip()]

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

    def _heuristic_debate_questions(self, query: str, position_a: str, position_b: str, depth: Depth) -> list[str]:
        base = [
            f"[A] What evidence most strongly supports this position: {position_a}?",
            f"[B] What evidence most strongly supports this position: {position_b}?",
            f"[SHARED] What core facts, definitions, and scope frame the debate about: {query}?",
            f"[SHARED] Where do sources directly disagree or show mixed evidence about: {query}?",
        ]
        if depth != Depth.QUICK:
            base.extend(
                [
                    f"[A] What recent developments strengthen or weaken: {position_a}?",
                    f"[B] What recent developments strengthen or weaken: {position_b}?",
                ]
            )
        if depth == Depth.DEEP:
            base.extend(
                [
                    f"[SHARED] Which sources are most credible on both sides of: {query}?",
                    f"[SHARED] What unresolved questions remain between {position_a} and {position_b}?",
                ]
            )
        return base[: self._max_questions(depth)]
