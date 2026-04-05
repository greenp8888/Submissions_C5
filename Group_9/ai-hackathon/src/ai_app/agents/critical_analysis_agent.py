from __future__ import annotations

from ai_app.agents.base import AgentBase
from ai_app.agents.contradiction_checker_agent import ContradictionCheckerAgent
from ai_app.agents.source_verifier_agent import SourceVerifierAgent
from ai_app.domain.enums import ConfidenceLabel
from ai_app.schemas.research import Claim, ResearchSession


class CriticalAnalysisAgent(AgentBase):
    name = "critical_analysis_agent"

    def __init__(self, source_verifier: SourceVerifierAgent, contradiction_checker: ContradictionCheckerAgent) -> None:
        self.source_verifier = source_verifier
        self.contradiction_checker = contradiction_checker

    async def run(self, session: ResearchSession) -> ResearchSession:
        await self.source_verifier.run(session)
        source_map = {source.id: source for source in session.sources}
        claims: list[Claim] = []
        for finding in session.findings:
            supports = list(finding.source_ids)
            support_sources = [source_map[source_id] for source_id in supports if source_id in source_map]
            avg_credibility = sum(source.credibility_score for source in support_sources) / max(1, len(support_sources))
            evidence_density = min(1.0, len(supports) / 3)
            confidence_pct = min(97, int(40 + (avg_credibility * 35) + (evidence_density * 22)))
            confidence = ConfidenceLabel.HIGH if confidence_pct >= 80 else ConfidenceLabel.MEDIUM if confidence_pct >= 60 else ConfidenceLabel.LOW
            contested = any(token in finding.content.lower() for token in ("controvers", "unclear", "debate", "mixed evidence", "contradict"))
            weak_evidence = len(supports) < 1 or avg_credibility < 0.58
            citation_parts: list[str] = []
            for source in support_sources[:3]:
                page_suffix = f" p.{','.join(str(page) for page in source.page_refs)}" if source.page_refs else ""
                citation_parts.append(f"{source.filename or source.title}{page_suffix}")
            citation_summary = ", ".join(citation_parts) or "Limited explicit source support"
            debate_position = self._infer_debate_position(finding.sub_question) if session.debate_mode else ""
            claims.append(
                Claim(
                    statement=finding.content.split(".")[0].strip() or finding.content[:120],
                    supporting_source_ids=supports,
                    confidence=confidence,
                    confidence_pct=confidence_pct,
                    reasoning="This claim is derived from retrieved evidence, then weighted by source credibility, date-fit, and corroboration.",
                    credibility_summary=f"Average source credibility {avg_credibility:.2f}; trusted because the cited sources were scored on provider quality, metadata completeness, date-window fit, and corroboration.",
                    evidence_summary=f"Primary evidence comes from {citation_summary}. Supporting snippet: {finding.quote_excerpt or finding.snippet or finding.content[:180]}",
                    contested=contested,
                    weak_evidence=weak_evidence,
                    trust_score=min(100, confidence_pct + (3 if avg_credibility > 0.75 else 0) - (5 if contested else 0)),
                    debate_position=debate_position,
                    consensus_pct=72 if contested else min(100, confidence_pct + 6),
                )
            )
        session.claims.extend(claims)
        contradictions = await self.contradiction_checker.run(session.claims, source_map)
        session.contradictions.extend(contradictions)
        self._apply_contradiction_metadata(session.claims, contradictions)
        return session

    def _infer_debate_position(self, sub_question: str) -> str:
        lowered = sub_question.lower()
        if lowered.startswith("[a]"):
            return "position_a"
        if lowered.startswith("[b]"):
            return "position_b"
        return "neutral"

    def _apply_contradiction_metadata(self, claims: list[Claim], contradictions) -> None:
        claim_map = {claim.id: claim for claim in claims}
        involvement_count: dict[str, int] = {}
        for contradiction in contradictions:
            for claim_id, opposing_source in (
                (contradiction.claim_a_id, contradiction.source_b_id),
                (contradiction.claim_b_id, contradiction.source_a_id),
            ):
                if not claim_id or claim_id not in claim_map:
                    continue
                claim = claim_map[claim_id]
                if opposing_source and opposing_source not in claim.contradicting_source_ids:
                    claim.contradicting_source_ids.append(opposing_source)
                claim.contested = True
                involvement_count[claim_id] = involvement_count.get(claim_id, 0) + 1

        for claim in claims:
            tension = involvement_count.get(claim.id, 0)
            if tension:
                claim.consensus_pct = max(28, min(claim.consensus_pct, 78 - (tension * 12)))
                claim.trust_score = max(18, claim.trust_score - (tension * 6))
            elif claim.contested:
                claim.consensus_pct = min(claim.consensus_pct, 72)
