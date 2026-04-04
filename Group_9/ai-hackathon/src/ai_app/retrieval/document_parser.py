from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


def checksum_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def parse_document(filename: str, content: bytes) -> tuple[str, int | None]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(BytesIO(content))
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts).strip(), len(reader.pages)
    if suffix in {".txt", ".md"}:
        return content.decode("utf-8", errors="ignore"), None
    return content.decode("utf-8", errors="ignore"), None
