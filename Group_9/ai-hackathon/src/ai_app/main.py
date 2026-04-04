from __future__ import annotations

import gradio as gr
from fastapi import FastAPI

from ai_app.api.health import router as health_router
from ai_app.api.knowledge import router as knowledge_router
from ai_app.api.research import router as research_router
from ai_app.config import get_settings
from ai_app.memory.session_store import SessionStore
from ai_app.orchestration.coordinator import ResearchCoordinator
from ui.gradio.deep_researcher import build_app


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.state.session_store = SessionStore()
    app.state.coordinator = ResearchCoordinator(settings, app.state.session_store)
    app.include_router(health_router)
    app.include_router(knowledge_router)
    app.include_router(research_router)
    demo = build_app(app.state.coordinator)
    app = gr.mount_gradio_app(app, demo, path="/")
    return app


app = create_app()
