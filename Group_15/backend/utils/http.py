import asyncio
import httpx
from typing import Optional

_client: Optional[httpx.AsyncClient] = None
_client_loop_id: Optional[int] = None


def get_client() -> httpx.AsyncClient:
    """
    Return an AsyncClient bound to the *current* asyncio event loop.

    Graph nodes call asyncio.run() per step, so each run uses a new loop. A
    singleton client created on an old loop triggers "Event loop is closed"
    on the next request when httpx cleans up connections.
    """
    global _client, _client_loop_id
    loop = asyncio.get_running_loop()
    loop_id = id(loop)
    if (
        _client is None
        or _client_loop_id != loop_id
        or getattr(_client, "is_closed", False)
    ):
        _client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "SignalForge/1.0 (Product Research Tool)"
            },
        )
        _client_loop_id = loop_id
    return _client


async def close_client():
    global _client, _client_loop_id
    if _client is not None and not getattr(_client, "is_closed", False):
        await _client.aclose()
    _client = None
    _client_loop_id = None
