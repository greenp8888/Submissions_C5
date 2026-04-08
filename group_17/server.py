from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
from contextlib import asynccontextmanager
import asyncio
import logging
import os
from orchestrator.graph import run_incident_analysis

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    port = os.getenv("API_PORT", "8000")
    mock = os.getenv("MOCK_MODE", "false").lower() == "true"
    mock_label = " [MOCK MODE — Slack/JIRA calls disabled]" if mock else ""
    logger.info("")
    logger.info("  ┌─────────────────────────────────────────────────────┐")
    logger.info("  │        DevOps Incident Analysis Suite API           │")
    logger.info("  ├─────────────────────────────────────────────────────┤")
    logger.info(f"  │  Swagger UI  →  http://localhost:{port}/docs          │")
    logger.info(f"  │  ReDoc       →  http://localhost:{port}/redoc         │")
    logger.info(f"  │  Health      →  http://localhost:{port}/health        │")
    logger.info(f"  │  Mode        →  {'mock' if mock else 'live'}{mock_label:<44}│")
    logger.info("  └─────────────────────────────────────────────────────┘")
    logger.info("")
    yield


app = FastAPI(
    title="DevOps Incident Analysis Suite",
    description=(
        "Multi-agent API that analyzes DevOps incident logs through a 5-agent "
        "LangGraph pipeline: Log Classifier → Remediation → Slack Notification → "
        "Cookbook Synthesizer → JIRA Ticket Agent."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request / Response models ────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    log_content: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "log_content": (
                        "2024-01-15 10:23:45 ERROR payment-service: "
                        "Database connection timeout after 30s\n"
                        "2024-01-15 10:23:46 CRITICAL api-gateway: "
                        "Service unavailable, upstream 503"
                    )
                }
            ]
        }
    }


class AnalyzeResponse(BaseModel):
    classified_logs: Optional[Any] = None
    remediation: Optional[Any] = None
    notification: Optional[Any] = None
    cookbook: Optional[Any] = None
    jira_tickets: Optional[Any] = None
    current_step: str
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    """Check that the API server is running."""
    return {"status": "ok", "version": app.version}


@app.post("/analyze", response_model=AnalyzeResponse, tags=["Pipeline"])
async def analyze(request: AnalyzeRequest):
    """
    Run the full 5-agent LangGraph pipeline on the provided log content.

    - **log_content**: Raw log text to analyze (paste log file contents here)

    Returns structured output from all 5 agents:
    - `classified_logs` — extracted issues with severity and affected services
    - `remediation` — root causes, fix steps, and bash commands per issue
    - `notification` — Slack message status and preview
    - `cookbook` — 4-phase incident runbook with escalation path
    - `jira_tickets` — created ticket IDs and links
    """
    if not request.log_content.strip():
        raise HTTPException(status_code=422, detail="log_content must not be empty")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, run_incident_analysis, request.log_content
    )
    return AnalyzeResponse(
        classified_logs=result.get("classified_logs"),
        remediation=result.get("remediation"),
        notification=result.get("notification"),
        cookbook=result.get("cookbook"),
        jira_tickets=result.get("jira_tickets"),
        current_step=result.get("current_step", "unknown"),
        error=result.get("error"),
    )


@app.post("/analyze/upload", response_model=AnalyzeResponse, tags=["Pipeline"])
async def analyze_upload(file: UploadFile = File(..., description="A .log or .txt file to analyze")):
    """
    Run the full 5-agent LangGraph pipeline by uploading a log file.

    Accepts `.log` or `.txt` files. Internally calls the same pipeline as `POST /analyze`.
    """
    if file.content_type not in ("text/plain", "application/octet-stream") and \
       not (file.filename or "").endswith((".log", ".txt")):
        raise HTTPException(
            status_code=415,
            detail="Only .log or .txt files are supported"
        )

    raw = await file.read()
    try:
        log_content = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=422, detail="File must be UTF-8 encoded text")

    if not log_content.strip():
        raise HTTPException(status_code=422, detail="Uploaded file is empty")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, run_incident_analysis, log_content
    )
    return AnalyzeResponse(
        classified_logs=result.get("classified_logs"),
        remediation=result.get("remediation"),
        notification=result.get("notification"),
        cookbook=result.get("cookbook"),
        jira_tickets=result.get("jira_tickets"),
        current_step=result.get("current_step", "unknown"),
        error=result.get("error"),
    )
