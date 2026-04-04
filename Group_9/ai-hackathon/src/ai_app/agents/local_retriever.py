from __future__ import annotations

from ai_app.agents.base import AgentBase
from ai_app.domain.enums import SourceType
from ai_app.retrieval.source_scoring import credibility_for_source
from ai_app.schemas.research import Finding, ResearchSession, Source
from ai_app.services.document_ingestion_service import DocumentIngestionService
from ai_app.retrieval.local_index import LocalIndex


class LocalRetriever(AgentBase):
    name = "local_retriever"

    def __init__(self, local_index: LocalIndex, ingestion_service: DocumentIngestionService, top_k: int) -> None:
        self.local_index = local_index
        self.ingestion_service = ingestion_service
        self.top_k = top_k

    async def run(self, session: ResearchSession, sub_question: str) -> tuple[list[Source], list[Finding]]:
        if not session.selected_collection_ids:
            return [], []
        chunks = self.local_index.search(session.selected_collection_ids, sub_question, self.top_k)
        session.retrieved_chunks.extend(chunks)
        sources: list[Source] = []
        findings: list[Finding] = []
        for chunk in chunks:
            source = Source(
                title=f"Local chunk {chunk.chunk_index}",
                source_type=SourceType.LOCAL_UPLOAD,
                provider="local_rag",
                snippet=chunk.text[:240],
                collection_id=session.selected_collection_ids[0],
                page_refs=chunk.page_span,
                relevance_score=0.9,
            )
            source.credibility_score = credibility_for_source(source)
            sources.append(source)
            findings.append(
                Finding(
                    sub_question=sub_question,
                    content=chunk.text[:400],
                    source_ids=[source.id],
                    agent=self.name,
                    raw={"chunk_id": chunk.id},
                )
            )
        return sources, findings

