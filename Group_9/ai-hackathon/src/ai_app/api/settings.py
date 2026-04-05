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
    openrouter_api_key = coordinator.settings.openrouter_api_key
    tavily_api_key = coordinator.settings.tavily_api_key
    if "openrouter_api_key" in payload.model_fields_set:
        openrouter_api_key = payload.openrouter_api_key
    if "tavily_api_key" in payload.model_fields_set:
        tavily_api_key = payload.tavily_api_key
    coordinator.update_provider_keys(
        openrouter_api_key,
        tavily_api_key,
        persist=payload.persist,
    )
    return coordinator.provider_settings_payload(include_values=False)
