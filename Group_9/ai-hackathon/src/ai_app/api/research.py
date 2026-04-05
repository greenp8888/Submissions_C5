from __future__ import annotations

import asyncio
import json
from datetime import date

from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi.responses import Response, StreamingResponse

from ai_app.domain.enums import DatePreset, RunMode, SourceChannel
from ai_app.schemas.report import ReportResponse
from ai_app.schemas.research import GraphResponse, ResearchRequest, TraceResponse

router = APIRouter(prefix="/api/research", tags=["research"])


def _parse_json_list(value: object, default: list[str] | None = None) -> list[str]:
    if value is None:
        return list(default or [])
    if isinstance(value, list):
        return [str(item) for item in value]
    text = str(value).strip()
    if not text:
        return list(default or [])
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        pass
    return [item.strip() for item in text.split(",") if item.strip()]


def _parse_date(value: object) -> date | None:
    if value in {None, "", "null"}:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


async def _parse_request(request: Request) -> tuple[ResearchRequest, list[tuple[str, bytes]]]:
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        query = str(form.get("query", ""))
        depth = str(form.get("depth", "standard"))
        collection_ids = _parse_json_list(form.get("collection_ids"), [])
        use_local_corpus = str(form.get("use_local_corpus", "true")).lower() == "true"
        enabled_sources = _parse_json_list(form.get("enabled_sources"), [])
        start_date = _parse_date(form.get("start_date"))
        end_date = _parse_date(form.get("end_date"))
        date_preset = str(form.get("date_preset", DatePreset.ALL_TIME.value))
        batch_topics = _parse_json_list(form.get("batch_topics"), [])
        run_mode = str(form.get("run_mode", RunMode.SINGLE.value))
        debate_enabled = str(form.get("debate_enabled", "false")).lower() == "true"
        position_a = str(form.get("position_a", "")).strip() or None
        position_b = str(form.get("position_b", "")).strip() or None
        files: list[tuple[str, bytes]] = []
        for value in form.getlist("files"):
            if isinstance(value, UploadFile):
                files.append((value.filename or "upload.txt", await value.read()))
        if not enabled_sources:
            enabled_sources = [SourceChannel.LOCAL_RAG.value, SourceChannel.WEB.value, SourceChannel.ARXIV.value]
        if not use_local_corpus:
            enabled_sources = [source for source in enabled_sources if source != SourceChannel.LOCAL_RAG.value]
        return (
            ResearchRequest(
                query=query,
                depth=depth,
                collection_ids=collection_ids,
                use_local_corpus=use_local_corpus,
                enabled_sources=enabled_sources,
                start_date=start_date,
                end_date=end_date,
                date_preset=date_preset,
                batch_topics=batch_topics,
                run_mode=run_mode,
                debate_enabled=debate_enabled,
                position_a=position_a,
                position_b=position_b,
            ),
            files,
        )
    payload = await request.json()
    if not payload.get("enabled_sources"):
        payload["enabled_sources"] = [SourceChannel.LOCAL_RAG.value, SourceChannel.WEB.value, SourceChannel.ARXIV.value]
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
