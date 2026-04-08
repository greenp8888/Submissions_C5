"""
FinanceDoctor — RAG Pipeline (Layer 2)
=======================================
Chunking → HuggingFace Embeddings → LanceDB Vector Store.

Uses sentence-transformers (free, local) for embeddings
and LanceDB (local, serverless) for vector storage.
"""

from __future__ import annotations

import os
from typing import Optional

import lancedb
import numpy as np
import pyarrow as pa
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import EMBED_MODEL_NAME, EMBED_DIM, LANCEDB_PATH, LANCEDB_TABLE, CHUNK_SIZE, CHUNK_OVERLAP


class RAGPipeline:
    """End-to-end RAG: ingest text → chunk → embed → store → query."""

    def __init__(self, db_path: str = LANCEDB_PATH):
        self.db_path = db_path
        self._embed_model: Optional[SentenceTransformer] = None
        self._db = None
        self._table = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", "|", ". ", ", ", " ", ""],
        )
        self._is_ingested = False

    # ── lazy loaders (avoid heavy init on import) ──────────

    @property
    def embed_model(self) -> SentenceTransformer:
        if self._embed_model is None:
            self._embed_model = SentenceTransformer(EMBED_MODEL_NAME)
        return self._embed_model

    @property
    def db(self):
        if self._db is None:
            os.makedirs(self.db_path, exist_ok=True)
            self._db = lancedb.connect(self.db_path)
        return self._db

    # ── INGEST ─────────────────────────────────────────────

    def ingest(self, text: str, source: str = "upload") -> int:
        """
        Chunk, embed, and store text in LanceDB.

        Returns:
            Number of chunks stored.
        """
        chunks = self.text_splitter.split_text(text)
        if not chunks:
            return 0

        # Encode all chunks in one batch
        embeddings = self.embed_model.encode(chunks, show_progress_bar=False)

        data = [
            {
                "text": chunk,
                "vector": embedding.tolist(),
                "source": source,
                "chunk_id": i,
            }
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]

        # Append or create the table
        if LANCEDB_TABLE in self.db.table_names():
            self._table = self.db.open_table(LANCEDB_TABLE)
            self._table.add(data)
        else:
            self._table = self.db.create_table(LANCEDB_TABLE, data)
        self._is_ingested = True
        return len(chunks)

    # ── QUERY ──────────────────────────────────────────────

    def query(self, question: str, top_k: int = 5) -> list[str]:
        """
        Embed the question and retrieve the top-k most relevant chunks.

        Returns:
            List of text chunks, most relevant first.
        """
        if not self._is_ingested:
            # Try to open existing table
            try:
                self._table = self.db.open_table(LANCEDB_TABLE)
                self._is_ingested = True
            except Exception:
                return []

        if self._table is None:
            return []

        query_vec = self.embed_model.encode([question], show_progress_bar=False)[0]
        try:
            results = (
                self._table
                .search(query_vec.tolist())
                .limit(top_k)
                .to_pandas()
            )
            return results["text"].tolist()
        except Exception:
            return []

    # ── INFO ───────────────────────────────────────────────

    @property
    def is_ready(self) -> bool:
        return self._is_ingested

    @property
    def chunk_count(self) -> int:
        if self._table is not None:
            try:
                return self._table.count_rows()
            except Exception:
                return 0
        return 0

    # ── CLEAR ──────────────────────────────────────────────

    def clear(self):
        """Drop the vector table and reset state."""
        try:
            self.db.drop_table(LANCEDB_TABLE)
        except Exception:
            pass
        self._table = None
        self._is_ingested = False
