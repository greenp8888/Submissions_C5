from __future__ import annotations

import json
from typing import Any

import httpx

from ai_app.config import Settings


class OpenRouterClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return bool(self.settings.openrouter_api_key)

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        if not self.enabled:
            return ""
        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.settings.openrouter_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.settings.openrouter_base_url}/chat/completions", headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError:
            return ""
        return data["choices"][0]["message"]["content"]

    async def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        text = await self.complete(system_prompt, user_prompt)
        if not text:
            return {}
        for candidate in _json_candidates(text):
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        return {}


def _json_candidates(text: str) -> list[str]:
    stripped = text.strip()
    candidates = [stripped]
    if "```" in stripped:
        segments = stripped.split("```")
        for segment in segments:
            cleaned = segment.strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
            if cleaned:
                candidates.append(cleaned)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(stripped[start : end + 1])
    return candidates
