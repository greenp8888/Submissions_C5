from __future__ import annotations

from ai_app.schemas.research import DocumentChunk


def chunk_text(document_id: str, text: str, page_span: list[int] | None = None, chunk_size: int = 700, overlap: int = 120) -> list[DocumentChunk]:
    clean = " ".join(text.split())
    if not clean:
        return []
    chunks: list[DocumentChunk] = []
    start = 0
    index = 0
    while start < len(clean):
        end = min(len(clean), start + chunk_size)
        snippet = clean[start:end]
        chunks.append(
            DocumentChunk(
                document_id=document_id,
                chunk_index=index,
                text=snippet,
                token_count=max(1, len(snippet.split())),
                page_span=page_span or [],
                keywords=sorted({word.lower() for word in snippet.split() if len(word) > 5})[:8],
            )
        )
        if end == len(clean):
            break
        start = max(0, end - overlap)
        index += 1
    return chunks

