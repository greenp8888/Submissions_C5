from __future__ import annotations

import asyncio

from ai_app.agents.academic_expansion_retriever import AcademicExpansionRetriever
from ai_app.agents.academic_retriever import AcademicRetriever
from ai_app.agents.base import AgentBase
from ai_app.agents.local_retriever import LocalRetriever
from ai_app.agents.news_expansion_retriever import NewsExpansionRetriever
from ai_app.agents.news_retriever import NewsRetriever
from ai_app.agents.pdf_retriever import PDFFallbackRetriever
from ai_app.agents.report_api_retriever import ReportAPIRetriever
from ai_app.agents.web_retriever import WebRetriever
from ai_app.domain.enums import Depth
from ai_app.retrieval.deduper import dedupe_sources
from ai_app.retrieval.source_scoring import rank_sources
from ai_app.schemas.research import Finding, ResearchSession, Source


class ContextualRetrieverAgent(AgentBase):
    name = "contextual_retriever_agent"

    def __init__(
        self,
        local_retriever: LocalRetriever,
        pdf_retriever: PDFFallbackRetriever,
        web_retriever: WebRetriever,
        news_retriever: NewsRetriever,
        academic_retriever: AcademicRetriever,
        academic_expansion_retriever: AcademicExpansionRetriever,
        news_expansion_retriever: NewsExpansionRetriever,
        report_api_retriever: ReportAPIRetriever,
        top_k: int,
    ) -> None:
        self.local_retriever = local_retriever
        self.pdf_retriever = pdf_retriever
        self.web_retriever = web_retriever
        self.news_retriever = news_retriever
        self.academic_retriever = academic_retriever
        self.academic_expansion_retriever = academic_expansion_retriever
        self.news_expansion_retriever = news_expansion_retriever
        self.report_api_retriever = report_api_retriever
        self.top_k = top_k

    async def run(self, session: ResearchSession) -> ResearchSession:
        all_sources: list[Source] = []
        all_findings: list[Finding] = []
        for sub_question in session.sub_questions:
            local_sources, local_findings = await self.local_retriever.run(session, sub_question)
            if not local_sources and session.pdf_texts:
                local_sources, local_findings = await self.pdf_retriever.run(session, sub_question)
            all_sources.extend(local_sources)
            all_findings.extend(local_findings)

            if len(local_findings) >= 2:
                continue

            tasks = [self.web_retriever.run(sub_question)]
            if session.depth != Depth.QUICK:
                tasks.extend(
                    [
                        self.news_retriever.run(sub_question),
                        self.academic_retriever.run(sub_question),
                    ]
                )
            if session.depth == Depth.DEEP:
                tasks.extend(
                    [
                        self.academic_expansion_retriever.run(sub_question),
                        self.news_expansion_retriever.run(sub_question),
                        self.report_api_retriever.run(sub_question),
                    ]
                )
            for sources, findings in await asyncio.gather(*tasks, return_exceptions=False):
                all_sources.extend(sources)
                all_findings.extend(findings)

        all_sources = rank_sources(dedupe_sources(all_sources))[: max(self.top_k * max(1, len(session.sub_questions)), self.top_k)]
        kept_ids = {source.id for source in all_sources}
        session.sources.extend(all_sources)
        session.findings.extend([finding for finding in all_findings if not finding.source_ids or any(source_id in kept_ids for source_id in finding.source_ids)])
        return session

