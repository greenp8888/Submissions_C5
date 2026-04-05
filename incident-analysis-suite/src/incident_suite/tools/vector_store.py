from __future__ import annotations

from pathlib import Path
from typing import Iterable

import lancedb
from langchain_text_splitters import RecursiveCharacterTextSplitter

from incident_suite.models.schemas import RetrievedChunk, SourceDocument


class IncidentVectorStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._db = lancedb.connect(db_path)

    def ingest(self, incident_id: str, documents: Iterable[SourceDocument]) -> list[RetrievedChunk]:
        splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=120)
        rows: list[dict] = []
        chunks: list[RetrievedChunk] = []
        for document in documents:
            for idx, chunk in enumerate(splitter.split_text(document.content or "")):
                row = {
                    "incident_id": incident_id,
                    "chunk_id": f"{document.doc_id}-chunk-{idx}",
                    "source_type": document.source_type,
                    "title": document.title,
                    "content": chunk,
                    "metadata": document.metadata,
                }
                rows.append(row)
                chunks.append(
                    RetrievedChunk(
                        chunk_id=row["chunk_id"],
                        content=chunk,
                        source_type=document.source_type,
                        score=1.0,
                        metadata=document.metadata,
                    )
                )
        if rows:
            table = self._db.create_table(f"incident_{incident_id}", data=rows, mode="overwrite")
            table.create_fts_index("content", replace=True)
        return chunks

    def search(self, incident_id: str, query: str, limit: int = 5) -> list[RetrievedChunk]:
        table_name = f"incident_{incident_id}"
        if table_name not in self._db.table_names():
            return []
        table = self._db.open_table(table_name)
        results = table.search(query, query_type="fts").limit(limit).to_list()
        return [
            RetrievedChunk(
                chunk_id=result["chunk_id"],
                content=result["content"],
                source_type=result["source_type"],
                score=float(result.get("_score", 1.0)),
                metadata=result.get("metadata", {}),
            )
            for result in results
        ]


def default_vector_store_path() -> str:
    root = Path(__file__).resolve().parents[3]
    db_dir = root / ".incident_lancedb"
    db_dir.mkdir(exist_ok=True)
    return str(db_dir)
