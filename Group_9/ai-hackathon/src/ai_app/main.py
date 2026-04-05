from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from ai_app.api.health import router as health_router
from ai_app.api.knowledge import router as knowledge_router
from ai_app.api.research import router as research_router
from ai_app.api.settings import router as settings_router
from ai_app.config import get_settings
from ai_app.memory.session_store import SessionStore
from ai_app.orchestration.coordinator import ResearchCoordinator


def frontend_dist_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "frontend" / "dist"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.state.session_store = SessionStore()
    app.state.coordinator = ResearchCoordinator(settings, app.state.session_store)
    app.include_router(health_router)
    app.include_router(knowledge_router)
    app.include_router(research_router)
    app.include_router(settings_router)

    dist_dir = frontend_dist_dir()
    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    async def spa_index():
        index_path = dist_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return HTMLResponse(
            """
            <html>
              <head><title>Frontend Not Built</title></head>
              <body style="font-family: sans-serif; padding: 2rem;">
                <h1>React frontend has not been built yet.</h1>
                <p>Run <code>npm install</code> and <code>npm run build</code> inside <code>frontend</code>, or use the updated start script.</p>
              </body>
            </html>
            """.strip()
        )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        if full_path.startswith("api") or full_path == "health":
            return HTMLResponse(status_code=404, content="Not found")
        file_path = dist_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        index_path = dist_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return HTMLResponse(status_code=404, content="Frontend build not found.")

    return app


app = create_app()
