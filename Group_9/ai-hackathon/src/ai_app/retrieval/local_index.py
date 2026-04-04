from __future__ import annotations

import json
from pathlib import Path

from ai_app.config import Settings
from ai_app.llms.embeddings import embed_text
from ai_app.schemas.research import DocumentChunk


class LocalIndex:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _collection_dir(self, collection_id: str) -> Path:
        path = self.settings.data_dir / "collections" / collection_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_chunks(self, collection_id: str, chunks: list[DocumentChunk]) -> None:
        existing = self.load_chunks(collection_id)
        payload = [chunk.model_dump(mode="json") for chunk in existing]
        for chunk in chunks:
            if not chunk.embedding:
                chunk.embedding = embed_text(chunk.text, dim=self.settings.embed_dim)
            payload.append(chunk.model_dump(mode="json"))
        path = self._collection_dir(collection_id) / "chunks.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load_chunks(self, collection_id: str) -> list[DocumentChunk]:
        path = self._collection_dir(collection_id) / "chunks.json"
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [DocumentChunk.model_validate(item) for item in payload]

    def search(self, collection_ids: list[str], query: str, top_k: int) -> list[DocumentChunk]:
        query_embedding = embed_text(query, dim=self.settings.embed_dim)
        scored: list[tuple[float, DocumentChunk]] = []
        for collection_id in collection_ids:
            for chunk in self.load_chunks(collection_id):
                if not chunk.embedding:
                    chunk.embedding = embed_text(chunk.text, dim=self.settings.embed_dim)
                score = sum(a * b for a, b in zip(query_embedding, chunk.embedding))
                scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]
