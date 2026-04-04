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
        claims: list[Claim] = []
        for finding in session.findings:
            supports = list(finding.source_ids)
            confidence_pct = min(95, 45 + (len(supports) * 15))
            confidence = ConfidenceLabel.HIGH if confidence_pct >= 80 else ConfidenceLabel.MEDIUM if confidence_pct >= 60 else ConfidenceLabel.LOW
            claims.append(
                Claim(
                    statement=finding.content.split(".")[0].strip() or finding.content[:120],
                    supporting_source_ids=supports,
                    confidence=confidence,
                    confidence_pct=confidence_pct,
                    reasoning="This claim is derived from retrieved evidence and weighted by source support.",
                    contested="controvers" in finding.content.lower() or "unclear" in finding.content.lower(),
                    weak_evidence=len(supports) < 1,
                    trust_score=min(100, confidence_pct + 5),
                )
            )
        session.claims.extend(claims)
        session.contradictions.extend(await self.contradiction_checker.run(claims))
        for claim in session.claims:
            if claim.contested:
                claim.contradicting_source_ids = claim.supporting_source_ids[:1]
        return session

