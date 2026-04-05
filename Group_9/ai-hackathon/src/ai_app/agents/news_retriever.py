from __future__ import annotations

from datetime import date

from ai_app.domain.enums import SourceType
from ai_app.agents.web_retriever import WebRetriever


class NewsRetriever(WebRetriever):
    name = "news_retriever"

    async def run(self, sub_question: str, start_date: date | None = None, end_date: date | None = None, max_results: int | None = None):
        if not self.settings.tavily_api_key:
            return [], []
        payload = {
            "api_key": self.settings.tavily_api_key,
            "query": sub_question if not start_date and not end_date else f"{sub_question} (news within {start_date or 'any'} to {end_date or 'today'})",
            "search_depth": "advanced",
            "topic": "news",
            "max_results": max_results or self.settings.top_k,
        }
        import httpx

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post("https://api.tavily.com/search", json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError:
            return [], []
        return self._convert(data.get("results", []), sub_question, SourceType.NEWS, start_date, end_date)
