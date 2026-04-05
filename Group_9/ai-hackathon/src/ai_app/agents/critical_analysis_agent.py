from __future__ import annotations

from ai_app.agents.base import AgentBase
from ai_app.agents.contradiction_checker_agent import ContradictionCheckerAgent
from ai_app.agents.llm_contracts import AnalysisOutput
from ai_app.agents.source_verifier_agent import SourceVerifierAgent
from ai_app.domain.enums import ConfidenceLabel
from ai_app.llms.client import OpenRouterClient
from ai_app.llms.prompts import load_prompt
from ai_app.llms.structured_output import parse_model
from ai_app.schemas.research import Claim, ResearchSession, Source


class CriticalAnalysisAgent(AgentBase):
    name = "critical_analysis_agent"

    def __init__(
        self,
        llm_client: OpenRouterClient,
        source_verifier: SourceVerifierAgent,
        contradiction_checker: ContradictionCheckerAgent,
    ) -> None:
        self.llm_client = llm_client
        self.source_verifier = source_verifier
        self.contradiction_checker = contradiction_checker
        self.system_prompt = load_prompt("system", "critical_analysis")

    async def run(self, session: ResearchSession) -> ResearchSession:
        await self.source_verifier.run(session)
        source_map = {source.id: source for source in session.sources}
        claims = await self._run_llm(session, source_map)
        if not claims:
            claims = self._heuristic_claims(session, source_map)
        session.claims.extend(claims)
        contradictions = await self.contradiction_checker.run(session.claims, source_map)
        session.contradictions.extend(contradictions)
        self._apply_contradiction_metadata(session.claims, contradictions)
        return session

    async def _run_llm(self, session: ResearchSession, source_map: dict[str, Source]) -> list[Claim]:
        if not self.llm_client.enabled or not session.findings:
            return []
        findings_payload = []
        for finding in session.findings[:18]:
            findings_payload.append(
                {
                    "id": finding.id,
                    "sub_question": finding.sub_question,
                    "content": finding.content,
                    "snippet": finding.snippet or finding.quote_excerpt,
                    "source_ids": finding.source_ids,
                    "debate_hint": self._infer_debate_position(finding.sub_question) if session.debate_mode else "neutral",
                }
            )
        user_prompt = (
            "Turn the retrieved findings into grounded research claims. "
            "Return JSON with key claims. Use only the provided source_ids and finding ids.\n"
            f"debate_mode={session.debate_mode}\n"
            f"findings={findings_payload}"
        )
        parsed = parse_model(await self.llm_client.complete_json(self.system_prompt, user_prompt), AnalysisOutput)
        if not parsed or not parsed.claims:
            return []
        claims: list[Claim] = []
        valid_source_ids = set(source_map.keys())
        finding_lookup = {finding.id: finding for finding in session.findings}
        for item in parsed.claims:
            supporting_source_ids = [source_id for source_id in item.supporting_source_ids if source_id in valid_source_ids]
            confidence_pct = max(0, min(100, item.confidence_pct))
            claims.append(
                Claim(
                    statement=item.statement.strip(),
                    supporting_source_ids=supporting_source_ids,
                    confidence=self._label_for_confidence(confidence_pct),
                    confidence_pct=confidence_pct,
                    reasoning=item.reasoning or "Structured analysis produced this claim from the retrieved evidence.",
                    credibility_summary=item.credibility_summary,
                    evidence_summary=item.evidence_summary,
                    contested=item.contested,
                    weak_evidence=item.weak_evidence,
                    trust_score=self._trust_from_sources(supporting_source_ids, source_map, confidence_pct, item.contested),
                    debate_position=item.debate_position or self._infer_position_from_findings(item.source_finding_ids, finding_lookup, session.debate_mode),
                    consensus_pct=max(0, min(100, item.consensus_pct or confidence_pct)),
                    source_finding_ids=[finding_id for finding_id in item.source_finding_ids if finding_id in finding_lookup],
                )
            )
        return [claim for claim in claims if claim.statement]

    def _heuristic_claims(self, session: ResearchSession, source_map: dict[str, Source]) -> list[Claim]:
        claims: list[Claim] = []
        for finding in session.findings:
            supports = list(finding.source_ids)
            support_sources = [source_map[source_id] for source_id in supports if source_id in source_map]
            avg_credibility = sum(source.credibility_score for source in support_sources) / max(1, len(support_sources))
            evidence_density = min(1.0, len(supports) / 3)
            confidence_pct = min(97, int(40 + (avg_credibility * 35) + (evidence_density * 22)))
            confidence = self._label_for_confidence(confidence_pct)
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
                    source_finding_ids=[finding.id],
                )
            )
        return claims

    def _label_for_confidence(self, confidence_pct: int) -> ConfidenceLabel:
        if confidence_pct >= 80:
            return ConfidenceLabel.HIGH
        if confidence_pct >= 60:
            return ConfidenceLabel.MEDIUM
        return ConfidenceLabel.LOW

    def _trust_from_sources(self, source_ids: list[str], source_map: dict[str, Source], confidence_pct: int, contested: bool) -> int:
        if not source_ids:
            return max(20, confidence_pct - 25)
        avg_credibility = sum(source_map[source_id].credibility_score for source_id in source_ids if source_id in source_map) / max(
            1,
            len([source_id for source_id in source_ids if source_id in source_map]),
        )
        return max(15, min(100, int((avg_credibility * 100 * 0.65) + (confidence_pct * 0.35) - (8 if contested else 0))))

    def _infer_debate_position(self, sub_question: str) -> str:
        lowered = sub_question.lower()
        if lowered.startswith("[a]"):
            return "position_a"
        if lowered.startswith("[b]"):
            return "position_b"
        return "neutral"

    def _infer_position_from_findings(self, finding_ids: list[str], finding_lookup: dict[str, object], debate_mode: bool) -> str:
        if not debate_mode:
            return ""
        for finding_id in finding_ids:
            finding = finding_lookup.get(finding_id)
            if not finding:
                continue
            position = self._infer_debate_position(finding.sub_question)
            if position != "neutral":
                return position
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
                claim.consensus_pct = min(claim.consensus_pct, contradiction.consensus_pct or claim.consensus_pct)
                involvement_count[claim_id] = involvement_count.get(claim_id, 0) + 1

        for claim in claims:
            tension = involvement_count.get(claim.id, 0)
            if tension:
                claim.consensus_pct = max(20, min(claim.consensus_pct, 78 - (tension * 12)))
                claim.trust_score = max(18, claim.trust_score - (tension * 6))
            elif claim.contested:
                claim.consensus_pct = min(claim.consensus_pct, 72)
