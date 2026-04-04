from __future__ import annotations

import httpx


class APIClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def get_json(self, path: str):
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}{path}")
            response.raise_for_status()
            return response.json()

