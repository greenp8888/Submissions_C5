from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from ai_app.schemas.research import KnowledgeUploadResponse, LocalCollection

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/upload", response_model=KnowledgeUploadResponse)
async def upload_knowledge(request: Request, collection_name: str, files: list[UploadFile] = File(...)):
    coordinator = request.app.state.coordinator
    collection = LocalCollection(name=collection_name)
    file_payloads = [(file.filename or "upload.txt", await file.read()) for file in files]
    documents, _ = coordinator.ingestion_service.ingest_files(collection, file_payloads)
    return KnowledgeUploadResponse(collection_id=collection.id, document_ids=[document.id for document in documents], status="indexed")


@router.get("/collections")
async def collections(request: Request):
    coordinator = request.app.state.coordinator
    return {"collections": coordinator.ingestion_service.list_collections()}


@router.get("/collections/{collection_id}")
async def collection_details(request: Request, collection_id: str):
    coordinator = request.app.state.coordinator
    try:
        collection, documents = coordinator.ingestion_service.collection_details(collection_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Collection not found") from exc
    return {"collection": collection, "documents": documents}

