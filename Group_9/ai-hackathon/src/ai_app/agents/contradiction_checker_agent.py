from __future__ import annotations

from ai_app.agents.base import AgentBase
from ai_app.schemas.research import Claim, Contradiction


class ContradictionCheckerAgent(AgentBase):
    name = "contradiction_checker_agent"

    async def run(self, claims: list[Claim]) -> list[Contradiction]:
        contradictions: list[Contradiction] = []
        for left in claims:
            for right in claims:
                if left.id >= right.id:
                    continue
                left_text = left.statement.lower()
                right_text = right.statement.lower()
                if any(word in left_text for word in ["not", "unclear", "controvers"]) and left_text != right_text:
                    contradictions.append(
                        Contradiction(
                            claim_a=left.statement,
                            source_a_id=left.supporting_source_ids[0] if left.supporting_source_ids else "",
                            claim_b=right.statement,
                            source_b_id=right.supporting_source_ids[0] if right.supporting_source_ids else "",
                            analysis="The evidence set contains tension or disagreement across sources.",
                        )
                    )
        return contradictions

