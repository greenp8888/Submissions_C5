from __future__ import annotations

from datetime import date

import httpx

from ai_app.agents.base import AgentBase
from ai_app.config import Settings
from ai_app.domain.enums import SourceType
from ai_app.retrieval.source_scoring import credibility_for_source
from ai_app.retrieval.time_filters import expand_query_with_date_window, matches_time_window
from ai_app.schemas.research import Finding, Source


class WebRetriever(AgentBase):
    name = "web_retriever"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def run(
        self,
        sub_question: str,
        start_date: date | None = None,
        end_date: date | None = None,
        max_results: int | None = None,
    ) -> tuple[list[Source], list[Finding]]:
        if not self.settings.tavily_api_key:
            return [], []
        query = expand_query_with_date_window(sub_question, start_date, end_date)
        payload = {
            "api_key": self.settings.tavily_api_key,
            "query": query,
            "search_depth": "advanced",
            "topic": "general",
            "max_results": max_results or self.settings.top_k,
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post("https://api.tavily.com/search", json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError:
            return [], []
        return self._convert(data.get("results", []), sub_question, SourceType.WEB, start_date, end_date)

    def _convert(
        self,
        results: list[dict],
        sub_question: str,
        source_type: SourceType,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> tuple[list[Source], list[Finding]]:
        sources: list[Source] = []
        findings: list[Finding] = []
        for item in results:
            published_date = item.get("published_date") or item.get("published") or item.get("date")
            matched_time_window = matches_time_window(published_date, start_date, end_date)
            if matched_time_window is False:
                continue
            source = Source(
                url=item.get("url"),
                title=item.get("title") or "Web source",
                source_type=source_type,
                provider="tavily",
                snippet=item.get("content", "")[:240],
                published_date=published_date,
                relevance_score=float(item.get("score", 0.5)),
                retrieval_reason=f"Retrieved from Tavily for sub-question: {sub_question}",
                matched_time_window=matched_time_window,
                metadata={"raw": item},
            )
            source.credibility_score = credibility_for_source(source)
            sources.append(source)
            findings.append(
                Finding(
                    sub_question=sub_question,
                    content=item.get("content", "")[:400],
                    snippet=item.get("content", "")[:240],
                    quote_excerpt=item.get("content", "")[:180],
                    source_ids=[source.id],
                    agent=self.name,
                    raw=item,
                )
            )
        return sources, findings
