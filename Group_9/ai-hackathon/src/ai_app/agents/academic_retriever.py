from __future__ import annotations

from datetime import date
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

import httpx

from ai_app.agents.base import AgentBase
from ai_app.domain.enums import SourceType
from ai_app.retrieval.source_scoring import credibility_for_source
from ai_app.retrieval.time_filters import matches_time_window
from ai_app.schemas.research import Finding, Source


class AcademicRetriever(AgentBase):
    name = "academic_retriever"

    async def run(
        self,
        sub_question: str,
        start_date: date | None = None,
        end_date: date | None = None,
        max_results: int = 5,
    ) -> tuple[list[Source], list[Finding]]:
        url = f"https://export.arxiv.org/api/query?search_query=all:{quote_plus(sub_question)}&start=0&max_results={max_results}"
        headers = {"User-Agent": "ai-hackathon-deep-researcher/0.1"}
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
        root = ET.fromstring(response.text)
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        sources: list[Source] = []
        findings: list[Finding] = []
        for entry in root.findall("atom:entry", namespace):
            title = (entry.findtext("atom:title", default="", namespaces=namespace) or "").strip()
            summary = (entry.findtext("atom:summary", default="", namespaces=namespace) or "").strip()
            link_el = entry.find("atom:id", namespace)
            published_date = entry.findtext("atom:published", default="", namespaces=namespace)
            matched_time_window = matches_time_window(published_date, start_date, end_date)
            if matched_time_window is False:
                continue
            source = Source(
                url=link_el.text if link_el is not None else None,
                title=title or "arXiv paper",
                source_type=SourceType.ACADEMIC,
                provider="arxiv",
                snippet=summary[:240],
                published_date=published_date,
                relevance_score=0.8,
                matched_time_window=matched_time_window,
                retrieval_reason=f"Retrieved from arXiv for sub-question: {sub_question}",
            )
            source.credibility_score = credibility_for_source(source)
            sources.append(source)
            findings.append(
                Finding(
                    sub_question=sub_question,
                    content=summary[:400],
                    snippet=summary[:240],
                    quote_excerpt=summary[:180],
                    source_ids=[source.id],
                    agent=self.name,
                    raw={},
                )
            )
        return sources, findings
