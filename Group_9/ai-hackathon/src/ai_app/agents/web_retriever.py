from __future__ import annotations

import httpx

from ai_app.agents.base import AgentBase
from ai_app.config import Settings
from ai_app.domain.enums import SourceType
from ai_app.retrieval.source_scoring import credibility_for_source
from ai_app.schemas.research import Finding, Source


class WebRetriever(AgentBase):
    name = "web_retriever"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def run(self, sub_question: str) -> tuple[list[Source], list[Finding]]:
        if not self.settings.tavily_api_key:
            return [], []
        payload = {
            "api_key": self.settings.tavily_api_key,
            "query": sub_question,
            "search_depth": "advanced",
            "topic": "general",
            "max_results": self.settings.top_k,
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post("https://api.tavily.com/search", json=payload)
            response.raise_for_status()
            data = response.json()
        return self._convert(data.get("results", []), sub_question, SourceType.WEB)

    def _convert(self, results: list[dict], sub_question: str, source_type: SourceType) -> tuple[list[Source], list[Finding]]:
        sources: list[Source] = []
        findings: list[Finding] = []
        for item in results:
            source = Source(
                url=item.get("url"),
                title=item.get("title") or "Web source",
                source_type=source_type,
                provider="tavily",
                snippet=item.get("content", "")[:240],
                relevance_score=float(item.get("score", 0.5)),
                metadata={"raw": item},
            )
            source.credibility_score = credibility_for_source(source)
            sources.append(source)
            findings.append(
                Finding(
                    sub_question=sub_question,
                    content=item.get("content", "")[:400],
                    source_ids=[source.id],
                    agent=self.name,
                    raw=item,
                )
            )
        return sources, findings

