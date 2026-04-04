from __future__ import annotations


def parse_sse_lines(payload: str) -> list[str]:
    return [line.removeprefix("data: ").strip() for line in payload.splitlines() if line.startswith("data: ")]

