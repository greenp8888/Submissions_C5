from __future__ import annotations

from langchain_openai import ChatOpenAI

from incident_suite.utils.settings import get_settings


def build_llm(
    api_key: str | None = None,
    model: str | None = None,
) -> ChatOpenAI | None:
    settings = get_settings()
    resolved_api_key = api_key or settings.openrouter_api_key
    resolved_model = model or settings.openrouter_model
    if not resolved_api_key:
        return None
    return ChatOpenAI(
        api_key=resolved_api_key,
        base_url=settings.openrouter_base_url,
        model=resolved_model,
        default_headers={
            "HTTP-Referer": settings.openrouter_site_url,
            "X-Title": settings.openrouter_app_name,
        },
        temperature=0.2,
    )
