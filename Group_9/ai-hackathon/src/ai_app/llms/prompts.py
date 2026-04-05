from __future__ import annotations

from functools import lru_cache
from pathlib import Path


@lru_cache
def load_prompt(group: str, name: str) -> str:
    path = prompts_dir() / group / f"{name}.txt"
    return path.read_text(encoding="utf-8").strip()


def prompts_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "prompts"
