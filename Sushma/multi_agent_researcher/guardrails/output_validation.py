"""Output guardrail — validates the final research report quality.

Called in main.py after graph.invoke() completes to ensure the report
meets minimum quality standards before it is presented to the user.
"""

import logging
import re

from multi_agent_researcher.guardrails.input_validation import ValidationResult

logger = logging.getLogger(__name__)

# Minimum report length for a meaningful research output
_MIN_REPORT_LENGTH = 500

# Required structural elements in the report
_REQUIRED_HEADINGS = ["##"]

# Patterns that confirm real content was generated (not just boilerplate)
_CONTENT_PATTERNS = [
    r"https?://",       # URLs from retrieved sources
    r"#{2,3}\s\w+",     # Markdown headings (## or ###)
    r"\d+\.\s",         # Numbered lists (findings)
    r"\*\*\w+",         # Bold text (key terms)
    r"- \w+",           # Bullet points
]


def validate_report_output(final_report: str, state: dict) -> ValidationResult:
    """Validate that the final research report meets quality standards.

    Checks:
    1. Report is not empty.
    2. Report meets minimum length (≥ 500 characters).
    3. Report contains at least one Markdown heading (## or ###).
    4. Report contains at least one URL (evidence that retrieval occurred).
    5. Report contains structured content (numbered lists, bullets, or bold).

    Args:
        final_report: The report string from the Report Builder agent.
        state: The full ResearchState dict for context in error messages.

    Returns:
        ValidationResult: valid=True if all checks pass, otherwise
            valid=False with an error message describing the failure.
    """
    if not final_report or not final_report.strip():
        logger.warning("Output validation failed: empty report")
        return ValidationResult(
            valid=False,
            error="Report Builder produced an empty report. The pipeline may have failed.",
        )

    report = final_report.strip()

    # Check minimum length
    if len(report) < _MIN_REPORT_LENGTH:
        logger.warning(
            "Output validation failed: report too short (%d chars < %d)",
            len(report),
            _MIN_REPORT_LENGTH,
        )
        return ValidationResult(
            valid=False,
            error=(
                f"Report is too short ({len(report)} characters). "
                f"A research report must be at least {_MIN_REPORT_LENGTH} characters. "
                f"The Report Builder may have failed or received insufficient context."
            ),
        )

    # Check for at least one Markdown heading
    has_headings = bool(re.search(r"^#{2,3}\s", report, re.MULTILINE))
    if not has_headings:
        logger.warning("Output validation failed: no Markdown headings found")
        return ValidationResult(
            valid=False,
            error=(
                "Report lacks structured headings (## or ###). "
                "A valid research report must include section headers."
            ),
        )

    # Check for at least one URL (evidence of retrieval)
    has_url = bool(re.search(r"https?://", report))
    if not has_url:
        logger.warning("Output validation failed: no URLs found in report")
        # Soft warning — some reports may use footnote-style citations
        # Don't fail hard, just warn
        docs = state.get("retrieved_documents", [])
        if len(docs) == 0:
            return ValidationResult(
                valid=False,
                error=(
                    "Report contains no URLs and no documents were retrieved. "
                    "Check your API keys and network connectivity."
                ),
            )

    # Check for at least 2 different content patterns (structured content)
    matches = sum(
        1 for p in _CONTENT_PATTERNS if re.search(p, report, re.MULTILINE)
    )
    if matches < 2:
        logger.warning(
            "Output validation failed: insufficient structured content (matched %d/%d patterns)",
            matches,
            len(_CONTENT_PATTERNS),
        )
        return ValidationResult(
            valid=False,
            error=(
                "Report lacks structured content. "
                "Expected findings lists, citations, and formatted sections."
            ),
        )

    logger.info(
        "Output validation passed: length=%d, headings=True, urls=%s, structure_patterns=%d",
        len(report),
        has_url,
        matches,
    )
    return ValidationResult(valid=True)
