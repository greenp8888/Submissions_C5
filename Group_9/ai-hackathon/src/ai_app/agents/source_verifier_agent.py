from __future__ import annotations

from ai_app.agents.base import AgentBase
from ai_app.retrieval.source_scoring import credibility_details
from ai_app.schemas.research import ResearchSession


class SourceVerifierAgent(AgentBase):
    name = "source_verifier_agent"

    async def run(self, session: ResearchSession) -> ResearchSession:
        source_to_questions: dict[str, set[str]] = {}
        question_to_sources: dict[str, set[str]] = {}
        for finding in session.findings:
            if not finding.source_ids:
                continue
            question_to_sources.setdefault(finding.sub_question, set()).update(finding.source_ids)
            for source_id in finding.source_ids:
                source_to_questions.setdefault(source_id, set()).add(finding.sub_question)
        for source in session.sources:
            related_questions = source_to_questions.get(source.id, set())
            agreement_samples = [len(question_to_sources.get(question, set())) for question in related_questions]
            agreement_score = min(1.0, (sum(agreement_samples) / max(1, len(agreement_samples) * 4))) if agreement_samples else 0.5
            source.credibility_score, source.credibility_explanation = credibility_details(source, agreement_score=agreement_score)
        return session
