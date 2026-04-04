from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi.responses import Response, StreamingResponse

from ai_app.schemas.report import ReportResponse
from ai_app.schemas.research import GraphResponse, ResearchRequest, TraceResponse

router = APIRouter(prefix="/api/research", tags=["research"])


async def _parse_request(request: Request) -> tuple[ResearchRequest, list[tuple[str, bytes]]]:
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        query = str(form.get("query", ""))
        depth = str(form.get("depth", "standard"))
        collection_ids = json.loads(str(form.get("collection_ids", "[]")))
        use_local_corpus = str(form.get("use_local_corpus", "true")).lower() == "true"
        files: list[tuple[str, bytes]] = []
        for value in form.getlist("files"):
            if isinstance(value, UploadFile):
                files.append((value.filename or "upload.txt", await value.read()))
        return ResearchRequest(query=query, depth=depth, collection_ids=collection_ids, use_local_corpus=use_local_corpus), files
    payload = await request.json()
    return ResearchRequest.model_validate(payload), []


@router.post("")
async def start_research(request: Request):
    coordinator = request.app.state.coordinator
    research_request, files = await _parse_request(request)
    session = await (coordinator.run_uploaded_research(research_request, files) if files else coordinator.start_background_research(research_request))
    return {"session_id": session.session_id, "status": "running"}


@router.get("/{session_id}/stream")
async def stream_research(request: Request, session_id: str):
    coordinator = request.app.state.coordinator
    queue = coordinator.session_store.queue(session_id)

    async def event_generator():
        while True:
            event = await queue.get()
            payload = event.model_dump_json()
            yield f"data: {payload}\n\n"
            if event.event_type in {"complete", "error"}:
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{session_id}/state")
async def research_state(request: Request, session_id: str):
    coordinator = request.app.state.coordinator
    try:
        return coordinator.session_store.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc


@router.get("/{session_id}/report", response_model=ReportResponse)
async def research_report(request: Request, session_id: str):
    coordinator = request.app.state.coordinator
    session = coordinator.session_store.get(session_id)
    return ReportResponse(sections=session.report_sections)


@router.get("/{session_id}/graph", response_model=GraphResponse)
async def research_graph(request: Request, session_id: str):
    coordinator = request.app.state.coordinator
    session = coordinator.session_store.get(session_id)
    return GraphResponse(nodes=session.entities, edges=session.relationships)


@router.get("/{session_id}/trace", response_model=TraceResponse)
async def research_trace(request: Request, session_id: str):
    coordinator = request.app.state.coordinator
    session = coordinator.session_store.get(session_id)
    return TraceResponse(trace=session.agent_trace)


@router.post("/{session_id}/dig-deeper")
async def dig_deeper(request: Request, session_id: str):
    coordinator = request.app.state.coordinator
    payload = await request.json()
    target_id = payload.get("finding_id") or payload.get("claim_id") or payload.get("insight_id")
    if not target_id:
        raise HTTPException(status_code=400, detail="finding_id, claim_id, or insight_id is required")
    await coordinator.dig_deeper(session_id, target_id)
    return {"session_id": session_id}


@router.get("/{session_id}/export/{fmt}")
async def export_report(request: Request, session_id: str, fmt: str):
    coordinator = request.app.state.coordinator
    session = coordinator.session_store.get(session_id)
    markdown = coordinator.report_service.render_markdown(session)
    if fmt == "markdown":
        return Response(content=coordinator.export_service.markdown_bytes(markdown), media_type="text/markdown")
    if fmt == "pdf":
        return Response(content=coordinator.export_service.pdf_bytes(markdown), media_type="application/pdf")
    raise HTTPException(status_code=400, detail="Unsupported format")

