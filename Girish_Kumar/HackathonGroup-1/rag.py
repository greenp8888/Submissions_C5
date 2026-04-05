"""
rag.py — Local RAG using HuggingFace sentence-transformers + FAISS.

Architecture
------------
1.  PDF text is extracted by pypdf (already done in research_engine).
2.  Text is chunked into overlapping windows.
3.  Each chunk is embedded by a local HuggingFace sentence-transformer model
    (runs entirely on CPU — no GPU required, no API key needed).
4.  Embeddings are stored in a FAISS flat-L2 index (in-memory).
5.  At query time the query is embedded with the same model and the top-k
    most-similar chunks are returned as augmented context.

Supported embedding models (all run locally via sentence-transformers):
    - "all-MiniLM-L6-v2"        ~80 MB  fastest, good quality     (default)
    - "all-mpnet-base-v2"       ~420 MB best quality, slower
    - "multi-qa-MiniLM-L6-cos-v1" ~80 MB tuned for Q&A retrieval
    - "BAAI/bge-small-en-v1.5"  ~130 MB strong, MTEB top performer
    - "BAAI/bge-base-en-v1.5"   ~440 MB larger BGE variant

Python 3.14+ compatible — no __future__ imports, fully parameterised generics.
"""

import re
import math
from typing import Any

# ── Optional heavy dependencies (graceful degradation) ───────────────────────
try:
    import numpy as np
    NUMPY_OK = True
except ImportError:
    NUMPY_OK = False

try:
    from sentence_transformers import SentenceTransformer
    ST_OK = True
except ImportError:
    ST_OK = False

try:
    import faiss
    FAISS_OK = True
except ImportError:
    FAISS_OK = False

RAG_AVAILABLE = NUMPY_OK and ST_OK and FAISS_OK

# Default model — small, fast, good quality, ~80 MB download on first use.
DEFAULT_EMBED_MODEL = "all-MiniLM-L6-v2"

# Recommended models exposed to the UI.
AVAILABLE_EMBED_MODELS: list[dict[str, str]] = [
    {
        "id":   "all-MiniLM-L6-v2",
        "label":"all-MiniLM-L6-v2  (~80 MB · fastest)",
        "note": "Best default. Fast CPU inference, strong general retrieval.",
    },
    {
        "id":   "multi-qa-MiniLM-L6-cos-v1",
        "label":"multi-qa-MiniLM-L6-cos-v1  (~80 MB · Q&A tuned)",
        "note": "Tuned for question-answering retrieval tasks.",
    },
    {
        "id":   "BAAI/bge-small-en-v1.5",
        "label":"BAAI/bge-small-en-v1.5  (~130 MB · strong)",
        "note": "Top MTEB performer at small scale. Recommended for research.",
    },
    {
        "id":   "BAAI/bge-base-en-v1.5",
        "label":"BAAI/bge-base-en-v1.5  (~440 MB · best quality)",
        "note": "Highest retrieval quality; slower first-load.",
    },
    {
        "id":   "all-mpnet-base-v2",
        "label":"all-mpnet-base-v2  (~420 MB · highest accuracy)",
        "note": "Best general-purpose quality; more RAM required.",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Chunking
# ─────────────────────────────────────────────────────────────────────────────

def _chunk_text(
    text: str,
    chunk_size: int = 400,
    overlap: int = 80,
) -> list[str]:
    """
    Split *text* into overlapping word-window chunks.

    Args:
        text:       Raw text to split.
        chunk_size: Target words per chunk.
        overlap:    Words shared between consecutive chunks.

    Returns:
        List of non-empty chunk strings.
    """
    # Normalise whitespace
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    step = max(1, chunk_size - overlap)
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# RAGIndex
# ─────────────────────────────────────────────────────────────────────────────

class RAGIndex:
    """
    In-memory vector index for PDF chunks.

    Usage
    -----
        idx = RAGIndex("all-MiniLM-L6-v2")
        idx.add_texts(["chunk one …", "chunk two …"])
        results = idx.query("What is the main finding?", top_k=5)
        # results → list of {"text": str, "score": float, "rank": int}

    The model is loaded once and reused for all add/query calls.
    First use triggers a one-time download from HuggingFace Hub (~80–440 MB
    depending on model). Subsequent runs load from the local cache.
    """

    def __init__(self, model_name: str = DEFAULT_EMBED_MODEL) -> None:
        if not RAG_AVAILABLE:
            missing = []
            if not NUMPY_OK:  missing.append("numpy")
            if not ST_OK:     missing.append("sentence-transformers")
            if not FAISS_OK:  missing.append("faiss-cpu")
            raise ImportError(
                f"Local RAG requires: pip install {' '.join(missing)}\n"
                "Install them and restart the app."
            )
        self.model_name = model_name
        self._model: SentenceTransformer | None = None
        self._index: Any | None = None          # faiss.IndexFlatL2
        self._chunks: list[str] = []
        self._dim: int = 0

    # ── Lazy model loader ─────────────────────────────────────────────────────
    @property
    def model(self) -> "SentenceTransformer":
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    # ── Build / add ───────────────────────────────────────────────────────────
    def add_texts(self, texts: list[str], batch_size: int = 64) -> int:
        """
        Embed *texts* and add them to the FAISS index.

        Returns the total number of chunks now in the index.
        """
        if not texts:
            return len(self._chunks)

        vecs = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,   # cosine via dot-product on L2 index
        ).astype("float32")

        dim = vecs.shape[1]
        if self._index is None:
            self._dim   = dim
            self._index = faiss.IndexFlatIP(dim)   # inner-product = cosine on normalised vecs
        elif dim != self._dim:
            raise ValueError(
                f"Embedding dim mismatch: index={self._dim}, new={dim}. "
                "Use the same model for all add_texts calls."
            )

        self._index.add(vecs)
        self._chunks.extend(texts)
        return len(self._chunks)

    def add_documents(
        self,
        docs: list[str],
        chunk_size: int = 400,
        overlap: int = 80,
    ) -> int:
        """
        Chunk each document in *docs* then embed and index all chunks.

        Returns total chunks indexed.
        """
        all_chunks: list[str] = []
        for doc in docs:
            all_chunks.extend(_chunk_text(doc, chunk_size, overlap))
        return self.add_texts(all_chunks)

    # ── Query ─────────────────────────────────────────────────────────────────
    def query(
        self,
        query_text: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Return the *top_k* most relevant chunks for *query_text*.

        Returns:
            List of dicts: {"text": str, "score": float, "rank": int}
            Sorted by descending similarity score.
        """
        if self._index is None or not self._chunks:
            return []

        top_k = min(top_k, len(self._chunks))

        q_vec = self.model.encode(
            [query_text],
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        scores, indices = self._index.search(q_vec, top_k)

        results: list[dict[str, Any]] = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), 1):
            if idx < 0:   # FAISS returns -1 for unfilled slots
                continue
            results.append({
                "text":  self._chunks[idx],
                "score": float(score),
                "rank":  rank,
            })
        return results

    # ── Helpers ───────────────────────────────────────────────────────────────
    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    def is_empty(self) -> bool:
        return self.chunk_count == 0

    def clear(self) -> None:
        """Reset the index (useful between pipeline runs)."""
        self._index  = None
        self._chunks = []

    def format_context(
        self,
        query_text: str,
        top_k: int = 5,
        max_chars: int = 4000,
    ) -> str:
        """
        Convenience method: query the index and return a formatted context
        string ready to be inserted into an LLM prompt.
        """
        hits = self.query(query_text, top_k=top_k)
        if not hits:
            return ""

        parts: list[str] = ["=== RELEVANT PDF CHUNKS (semantic search) ===\n"]
        total = 0
        for hit in hits:
            chunk_str = (
                f"[Chunk {hit['rank']} · similarity {hit['score']:.3f}]\n"
                f"{hit['text']}\n"
            )
            if total + len(chunk_str) > max_chars:
                break
            parts.append(chunk_str)
            total += len(chunk_str)
        return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# Module-level convenience
# ─────────────────────────────────────────────────────────────────────────────

def build_rag_index(
    pdf_texts: list[str],
    model_name: str = DEFAULT_EMBED_MODEL,
    chunk_size: int = 400,
    overlap: int = 80,
) -> RAGIndex | None:
    """
    Build a RAGIndex from a list of already-extracted PDF text strings.

    Returns None (with a warning) if RAG dependencies are not installed.
    """
    if not RAG_AVAILABLE:
        return None
    idx = RAGIndex(model_name)
    idx.add_documents(pdf_texts, chunk_size=chunk_size, overlap=overlap)
    return idx


def rag_availability_message() -> str:
    """Human-readable status string shown in the UI."""
    if RAG_AVAILABLE:
        return "✅ Local RAG ready (sentence-transformers + FAISS)"
    missing = []
    if not ST_OK:     missing.append("`sentence-transformers`")
    if not FAISS_OK:  missing.append("`faiss-cpu`")
    if not NUMPY_OK:  missing.append("`numpy`")
    return (
        "⚠️ Local RAG disabled — install: "
        + ", ".join(missing)
        + "\n`pip install sentence-transformers faiss-cpu`"
    )