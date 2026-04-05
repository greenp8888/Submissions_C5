from __future__ import annotations

from ai_app.agents.base import AgentBase
from ai_app.agents.llm_contracts import QAReviewOutput
from ai_app.llms.client import OpenRouterClient
from ai_app.llms.prompts import load_prompt
from ai_app.llms.structured_output import parse_model
from ai_app.schemas.research import ResearchSession


class QAReviewAgent(AgentBase):
    name = "qa_review_agent"

    def __init__(self, llm_client: OpenRouterClient) -> None:
        self.llm_client = llm_client
        self.system_prompt = load_prompt("system", "qa_review")

    async def run(self, session: ResearchSession) -> ResearchSession:
        review = await self._run_llm(session)
        if review is None:
            review = self._heuristic_review(session)
        session.metadata["qa_review"] = review
        return session

    async def _run_llm(self, session: ResearchSession) -> dict[str, object] | None:
        if not self.llm_client.enabled:
            return None
        payload = {
            "query": session.query,
            "claims": [
                {
                    "id": claim.id,
                    "statement": claim.statement,
                    "confidence_pct": claim.confidence_pct,
                    "trust_score": claim.trust_score,
                    "supporting_source_count": len(claim.supporting_source_ids),
                    "contradicting_source_count": len(claim.contradicting_source_ids),
                }
                for claim in session.claims[:14]
            ],
            "contradictions": len(session.contradictions),
            "report_sections": [section.title for section in session.report_sections],
        }
        parsed = parse_model(
            await self.llm_client.complete_json(
                self.system_prompt,
                "Review the research output for unsupported claims, citation gaps, unresolved contradictions, and missing limitations. "
                "Return JSON with verdict, summary, and warnings.\n"
                f"payload={payload}",
            ),
            QAReviewOutput,
        )
        if not parsed:
            return None
        return parsed.model_dump(mode="json")

    def _heuristic_review(self, session: ResearchSession) -> dict[str, object]:
        warnings: list[dict[str, object]] = []
        weak_claims = [claim for claim in session.claims if not claim.supporting_source_ids or claim.trust_score < 45]
        if weak_claims:
            warnings.append(
                {
                    "severity": "medium",
                    "message": "Some claims remain weakly supported or lightly cited.",
                    "related_claim_ids": [claim.id for claim in weak_claims[:6]],
                }
            )
        if session.contradictions and not any(section.section_type == "contested" for section in session.report_sections):
            warnings.append(
                {
                    "severity": "high",
                    "message": "Contradictions were detected but not fully surfaced in the report structure.",
                    "related_claim_ids": [],
                }
            )
        verdict = "pass" if not warnings else "review_with_warnings"
        return {
            "verdict": verdict,
            "summary": "Heuristic QA review completed." if not warnings else "Heuristic QA review found items that deserve attention.",
            "warnings": warnings,
        }
