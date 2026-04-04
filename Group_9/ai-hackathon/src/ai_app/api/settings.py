from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter(prefix="/api/settings", tags=["settings"])


class ProviderSettingsPayload(BaseModel):
    openrouter_api_key: str | None = None
    tavily_api_key: str | None = None
    persist: bool = True


@router.get("/providers")
async def get_provider_settings(request: Request):
    coordinator = request.app.state.coordinator
    return coordinator.provider_settings_payload(include_values=False)


@router.post("/providers")
async def update_provider_settings(request: Request, payload: ProviderSettingsPayload):
    coordinator = request.app.state.coordinator
    coordinator.update_provider_keys(
        payload.openrouter_api_key,
        payload.tavily_api_key,
        persist=payload.persist,
    )
    return coordinator.provider_settings_payload(include_values=False)
