"""Input guardrail — validates research queries before pipeline invocation.

Called in main.py before graph.invoke() to catch invalid inputs early
and provide clear, actionable error messages rather than cryptic failures
deep inside the pipeline.
"""

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Minimum query length for a meaningful research investigation
_MIN_QUERY_LENGTH = 15

# Maximum query length to avoid LLM context issues in the planner
_MAX_QUERY_LENGTH = 2000


@dataclass
class ValidationResult:
    """Result of an input or output validation check.

    Attributes:
        valid: True if the check passed.
        error: Human-readable error message when valid is False.
    """

    valid: bool
    error: str = ""


def validate_research_input(query: str, config: dict) -> ValidationResult:
    """Validate that the research query and configuration are ready for the pipeline.

    Checks:
    1. Query is not empty.
    2. Query meets minimum length (≥ 15 characters).
    3. Query does not exceed maximum length (≤ 2000 characters).
    4. TAVILY_API_KEY is configured (minimum viable retrieval source).
    5. OPENROUTER_API_KEY is configured (required for all LLM calls).

    Args:
        query: The raw user research question.
        config: Configuration dict from load_config().

    Returns:
        ValidationResult: valid=True if all checks pass, otherwise
            valid=False with an error message explaining the issue.
    """
    # Check query exists
    if not query or not query.strip():
        logger.warning("Input validation failed: empty query")
        return ValidationResult(
            valid=False,
            error="Research query is empty. Please provide a research question.",
        )

    stripped = query.strip()

    # Check minimum length
    if len(stripped) < _MIN_QUERY_LENGTH:
        logger.warning(
            "Input validation failed: query too short (%d chars < %d)",
            len(stripped),
            _MIN_QUERY_LENGTH,
        )
        return ValidationResult(
            valid=False,
            error=(
                f"Research query is too short ({len(stripped)} characters). "
                f"Please provide at least {_MIN_QUERY_LENGTH} characters "
                f"for a meaningful research investigation."
            ),
        )

    # Check maximum length
    if len(stripped) > _MAX_QUERY_LENGTH:
        logger.warning(
            "Input validation failed: query too long (%d chars > %d)",
            len(stripped),
            _MAX_QUERY_LENGTH,
        )
        return ValidationResult(
            valid=False,
            error=(
                f"Research query is too long ({len(stripped)} characters). "
                f"Please keep it under {_MAX_QUERY_LENGTH} characters."
            ),
        )

    # Check Tavily API key (minimum retrieval source)
    tavily_key = config.get("tavily_api_key") or os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        logger.warning("Input validation failed: TAVILY_API_KEY not set")
        return ValidationResult(
            valid=False,
            error=(
                "TAVILY_API_KEY is not configured. "
                "Tavily is the primary web search source. "
                "Add it to your .env file: TAVILY_API_KEY=your_key_here\n"
                "Get a free key at: https://tavily.com"
            ),
        )

    # Check OpenRouter API key (required for all LLM calls)
    openrouter_key = config.get("openrouter_api_key") or os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        logger.warning("Input validation failed: OPENROUTER_API_KEY not set")
        return ValidationResult(
            valid=False,
            error=(
                "OPENROUTER_API_KEY is not configured. "
                "This key is required for all agent LLM calls. "
                "Add it to your .env file: OPENROUTER_API_KEY=your_key_here\n"
                "Get a key at: https://openrouter.ai"
            ),
        )

    logger.info(
        "Input validation passed: query_length=%d, tavily=configured, openrouter=configured",
        len(stripped),
    )
    return ValidationResult(valid=True)
