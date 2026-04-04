from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar


T = TypeVar("T")


async def with_retries(func: Callable[[], Awaitable[T]], retries: int = 2, delay: float = 0.5) -> T:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return await func()
        except Exception as exc:  # pragma: no cover - best effort retry helper
            last_error = exc
            if attempt == retries:
                raise
            await asyncio.sleep(delay)
    raise RuntimeError("retry helper exhausted") from last_error

