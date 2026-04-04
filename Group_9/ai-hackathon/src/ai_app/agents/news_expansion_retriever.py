from __future__ import annotations

from ai_app.agents.base import AgentBase


class NewsExpansionRetriever(AgentBase):
    name = "news_expansion_retriever"

    async def run(self, sub_question: str):
        return [], []

