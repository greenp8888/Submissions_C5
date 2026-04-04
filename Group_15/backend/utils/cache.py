import time
from typing import Optional, Any
from functools import wraps

_cache: dict[str, tuple[float, Any]] = {}
TTL = 1800


def cache_key(idea: str, audience: str) -> str:
    return f"{idea.strip().lower()}::{audience.strip().lower()}"


def get_cached_report(idea: str, audience: str) -> Optional[dict]:
    key = cache_key(idea, audience)
    if key in _cache:
        timestamp, value = _cache[key]
        if time.time() - timestamp < TTL:
            return value
        else:
            del _cache[key]
    return None


def cache_report(idea: str, audience: str, report: dict):
    key = cache_key(idea, audience)
    _cache[key] = (time.time(), report)


def clear_expired():
    now = time.time()
    expired_keys = [k for k, (ts, _) in _cache.items() if now - ts >= TTL]
    for k in expired_keys:
        del _cache[k]
