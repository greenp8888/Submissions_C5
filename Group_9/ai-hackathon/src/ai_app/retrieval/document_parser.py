from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


def checksum_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def parse_document_pages(filename: str, content: bytes) -> tuple[str, list[tuple[int, str]], int | None]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(BytesIO(content))
        pages: list[tuple[int, str]] = []
        for index, page in enumerate(reader.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            if page_text:
                pages.append((index, page_text))
        full_text = "\n\n".join(page_text for _, page_text in pages).strip()
        return full_text, pages, len(reader.pages)
    text = content.decode("utf-8", errors="ignore")
    return text, [], None


def parse_document(filename: str, content: bytes) -> tuple[str, int | None]:
    text, _, page_count = parse_document_pages(filename, content)
    return text, page_count
