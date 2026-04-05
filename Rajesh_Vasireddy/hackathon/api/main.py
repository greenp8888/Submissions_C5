"""FastAPI application entry-point."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (same directory as this file's parent)
# This works regardless of the working directory uvicorn is started from.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from api.schemas import HealthResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

# Startup env-var check — logs what is and isn't configured
_REQUIRED = ["OPENROUTER_API_KEY"]
_OPTIONAL = ["SLACK_WEBHOOK_URL", "JIRA_URL", "JIRA_USER", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"]

for _var in _REQUIRED:
    if os.getenv(_var):
        logger.info("ENV ✓  %s is set", _var)
    else:
        logger.error("ENV ✗  %s is MISSING — pipeline will fail", _var)

for _var in _OPTIONAL:
    logger.info("ENV %s  %s", "✓" if os.getenv(_var) else "–", _var)

app = FastAPI(
    title="DevOps Incident Suite API",
    description="AI-powered log analysis and remediation pipeline.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow the Streamlit frontend (running on a different port) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="")


@app.get("/healthz", response_model=HealthResponse, tags=["ops"])
async def health_check():
    """Liveness probe."""
    return HealthResponse()
