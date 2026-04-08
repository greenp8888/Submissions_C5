"""utils.py — Shared utility functions."""

import re


def format_report_as_markdown(report_text: str) -> str:
    """Ensure the report is clean markdown (no extra fence blocks etc.)."""
    # Strip any triple-backtick fences that the LLM might add
    report_text = re.sub(r"```(?:markdown|md)?\n?", "", report_text)
    report_text = report_text.replace("```", "")
    return report_text.strip()


def truncate(text: str, max_chars: int = 500) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"


def count_words(text: str) -> int:
    return len(text.split())
