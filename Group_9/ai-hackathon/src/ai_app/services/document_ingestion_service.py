from __future__ import annotations

import json
from pathlib import Path

from ai_app.config import Settings
from ai_app.retrieval.chunking import chunk_text
from ai_app.retrieval.document_parser import checksum_bytes, parse_document_pages
from ai_app.retrieval.local_index import LocalIndex
from ai_app.schemas.research import DocumentChunk, KnowledgeDocument, LocalCollection


class DocumentIngestionService:
    def __init__(self, settings: Settings, local_index: LocalIndex) -> None:
        self.settings = settings
        self.local_index = local_index

    def _collection_dir(self, collection_id: str) -> Path:
        path = self.settings.data_dir / "collections" / collection_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_collection(self, collection: LocalCollection) -> None:
        path = self._collection_dir(collection.id) / "collection.json"
        path.write_text(collection.model_dump_json(indent=2), encoding="utf-8")

    def list_collections(self) -> list[LocalCollection]:
        collections: list[LocalCollection] = []
        for path in (self.settings.data_dir / "collections").glob("*/collection.json"):
            collections.append(LocalCollection.model_validate_json(path.read_text(encoding="utf-8")))
        return sorted(collections, key=lambda item: item.created_at, reverse=True)

    def collection_details(self, collection_id: str) -> tuple[LocalCollection, list[KnowledgeDocument]]:
        collection = LocalCollection.model_validate_json((self._collection_dir(collection_id) / "collection.json").read_text(encoding="utf-8"))
        doc_path = self._collection_dir(collection_id) / "documents.json"
        payload = json.loads(doc_path.read_text(encoding="utf-8")) if doc_path.exists() else []
        documents = [KnowledgeDocument.model_validate(item) for item in payload]
        return collection, documents

    def document_lookup(self, collection_ids: list[str]) -> dict[str, KnowledgeDocument]:
        lookup: dict[str, KnowledgeDocument] = {}
        for collection_id in collection_ids:
            try:
                _, documents = self.collection_details(collection_id)
            except FileNotFoundError:
                continue
            for document in documents:
                lookup[document.id] = document
        return lookup

    def ingest_files(self, collection: LocalCollection, files: list[tuple[str, bytes]], tags: list[str] | None = None) -> tuple[list[KnowledgeDocument], list[DocumentChunk]]:
        documents: list[KnowledgeDocument] = []
        chunks: list[DocumentChunk] = []
        collection_dir = self._collection_dir(collection.id)
        existing_documents_path = collection_dir / "documents.json"
        existing_documents_payload = json.loads(existing_documents_path.read_text(encoding="utf-8")) if existing_documents_path.exists() else []
        existing_documents = [KnowledgeDocument.model_validate(item) for item in existing_documents_payload]
        for filename, content in files:
            text, parsed_pages, page_count = parse_document_pages(filename, content)
            document = KnowledgeDocument(
                collection_id=collection.id,
                filename=filename,
                document_type=Path(filename).suffix.lower().lstrip(".") or "txt",
                checksum=checksum_bytes(content),
                page_count=page_count,
                tags=tags or [],
                status="indexed",
                summary=" ".join(text.split())[:280],
            )
            doc_chunks: list[DocumentChunk] = []
            if parsed_pages:
                for page_number, page_text in parsed_pages:
                    doc_chunks.extend(chunk_text(document.id, page_text, page_span=[page_number]))
            else:
                doc_chunks = chunk_text(document.id, text, page_span=[])
            for chunk_index, chunk in enumerate(doc_chunks):
                chunk.chunk_index = chunk_index
            documents.append(document)
            chunks.extend(doc_chunks)
            collection.document_ids.append(document.id)
        self.save_collection(collection)
        existing_documents.extend(documents)
        existing_documents_path.write_text(
            json.dumps([document.model_dump(mode="json") for document in existing_documents], indent=2),
            encoding="utf-8",
        )
        self.local_index.save_chunks(collection.id, chunks)
        return documents, chunks
