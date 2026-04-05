from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/docs", tags=["docs"])

DOC_MAP = {
    "project-reference": Path("README.md"),
    "architecture": Path("docs/ARCHITECTURE.md"),
    "workflows": Path("docs/WORKFLOW_DIAGRAMS.md"),
}


@router.get("/{doc_name}")
async def read_doc(doc_name: str):
    if doc_name not in DOC_MAP:
        raise HTTPException(status_code=404, detail="Document not found")
    root = Path(__file__).resolve().parents[3]
    path = root / DOC_MAP[doc_name]
    if not path.exists():
        raise HTTPException(status_code=404, detail="Document file missing")
    return {"name": doc_name, "title": path.name, "content": path.read_text(encoding="utf-8")}
