from __future__ import annotations

from collections import Counter

from ai_app.agents.base import AgentBase
from ai_app.schemas.research import Claim, Contradiction, Source


class ContradictionCheckerAgent(AgentBase):
    name = "contradiction_checker_agent"

    async def run(self, claims: list[Claim], source_map: dict[str, Source]) -> list[Contradiction]:
        contradictions: list[Contradiction] = []
        for index, left in enumerate(claims):
            for right in claims[index + 1 :]:
                if left.id == right.id:
                    continue
                if not self._looks_related(left.statement, right.statement):
                    continue
                if not self._shows_tension(left, right):
                    continue
                left_source_id = left.supporting_source_ids[0] if left.supporting_source_ids else ""
                right_source_id = right.supporting_source_ids[0] if right.supporting_source_ids else ""
                left_source = source_map.get(left_source_id)
                right_source = source_map.get(right_source_id)
                left_label = self._source_label(left_source)
                right_label = self._source_label(right_source)
                lean = self._credibility_lean(left, right, left_source, right_source)
                rationale = self._weighting_rationale(left, right, left_source, right_source, lean)
                if left.statement != right.statement:
                    contradictions.append(
                        Contradiction(
                            claim_a_id=left.id,
                            claim_a=left.statement,
                            source_a_id=left_source_id,
                            source_a_label=left_label,
                            claim_b_id=right.id,
                            claim_b=right.statement,
                            source_b_id=right_source_id,
                            source_b_label=right_label,
                            analysis="The evidence set contains tension or disagreement across sources.",
                            credibility_lean=lean,
                            weighting_rationale=rationale,
                        )
                    )
        return contradictions

    def _looks_related(self, left_text: str, right_text: str) -> bool:
        left_words = {word for word in self._keywords(left_text) if len(word) > 3}
        right_words = {word for word in self._keywords(right_text) if len(word) > 3}
        return bool(left_words & right_words)

    def _shows_tension(self, left: Claim, right: Claim) -> bool:
        opposing_positions = left.debate_position and right.debate_position and left.debate_position != right.debate_position
        weak_or_contested = left.contested or right.contested or left.weak_evidence or right.weak_evidence
        polarity_gap = abs(left.confidence_pct - right.confidence_pct) >= 12
        tension_tokens = ("not", "unclear", "mixed", "controvers", "disagree", "limited", "uncertain", "however")
        left_text = left.statement.lower()
        right_text = right.statement.lower()
        textual_tension = any(token in left_text or token in right_text for token in tension_tokens)
        return bool(opposing_positions or weak_or_contested or polarity_gap or textual_tension)

    def _keywords(self, text: str) -> list[str]:
        cleaned = "".join(character if character.isalnum() else " " for character in text.lower())
        return [part for part in cleaned.split() if part]

    def _source_label(self, source: Source | None) -> str:
        if not source:
            return "Unlabeled source"
        base = source.filename or source.title
        return f"{base} [{source.provider}]"

    def _credibility_lean(self, left: Claim, right: Claim, left_source: Source | None, right_source: Source | None) -> str:
        left_score = (left.trust_score / 100) + (left_source.credibility_score if left_source else 0)
        right_score = (right.trust_score / 100) + (right_source.credibility_score if right_source else 0)
        if abs(left_score - right_score) < 0.08:
            return "mixed"
        if left.debate_position in {"position_a", "position_b"} and left_score > right_score:
            return left.debate_position
        if right.debate_position in {"position_a", "position_b"} and right_score > left_score:
            return right.debate_position
        return "claim_a" if left_score > right_score else "claim_b"

    def _weighting_rationale(self, left: Claim, right: Claim, left_source: Source | None, right_source: Source | None, lean: str) -> str:
        provider_bias = Counter(filter(None, [left_source.provider if left_source else None, right_source.provider if right_source else None]))
        provider_note = ", ".join(f"{provider}={count}" for provider, count in provider_bias.items()) or "provider data unavailable"
        return (
            f"Weighted toward {lean} using trust score, source credibility, and corroboration patterns. "
            f"Claim A trust={left.trust_score}%, Claim B trust={right.trust_score}%. Providers: {provider_note}."
        )
