from __future__ import annotations

from ai_app.agents.base import AgentBase


class ReportAPIRetriever(AgentBase):
    name = "report_api_retriever"

    async def run(self, sub_question: str):
        return [], []

