from __future__ import annotations

from ai_app.agents.base import AgentBase
from ai_app.domain.enums import SourceType
from ai_app.retrieval.source_scoring import credibility_for_source
from ai_app.schemas.research import Finding, ResearchSession, Source


class PDFFallbackRetriever(AgentBase):
    name = "pdf_retriever"

    async def run(self, session: ResearchSession, sub_question: str) -> tuple[list[Source], list[Finding]]:
        if not session.pdf_texts:
            return [], []
        findings: list[Finding] = []
        sources: list[Source] = []
        for index, text in enumerate(session.pdf_texts[:2], start=1):
            snippet = " ".join(text.split())[:400]
            source = Source(
                title=f"Uploaded PDF fallback {index}",
                source_type=SourceType.PDF,
                provider="pdf_fallback",
                snippet=snippet,
                page_refs=[1],
                relevance_score=0.75,
            )
            source.credibility_score = credibility_for_source(source)
            sources.append(source)
            findings.append(Finding(sub_question=sub_question, content=snippet, source_ids=[source.id], agent=self.name, raw={}))
        return sources, findings

