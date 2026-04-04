from __future__ import annotations

from ai_app.agents.base import AgentBase


class AcademicExpansionRetriever(AgentBase):
    name = "academic_expansion_retriever"

    async def run(self, sub_question: str):
        return [], []

