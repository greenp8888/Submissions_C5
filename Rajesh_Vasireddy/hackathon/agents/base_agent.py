"""Base agent with shared LLM API call and retry logic."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

import openai
from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, RateLimitError


def extract_json_payload(raw: str) -> str:
    """Normalize model output and extract JSON payload from text."""
    raw = raw.strip()

    # Remove markdown code fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)

    # Try to find JSON object/array at the start
    raw = raw.lstrip()

    decoder = json.JSONDecoder()
    for idx, char in enumerate(raw):
        if char not in "[{":
            continue
        try:
            _, end = decoder.raw_decode(raw[idx:])
            json_str = raw[idx : idx + end]
            # Validate it's proper JSON by re-encoding
            parsed = json.loads(json_str)
            return json.dumps(parsed)
        except json.JSONDecodeError:
            continue

    raise json.JSONDecodeError("No JSON object could be decoded", raw, 0)

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "anthropic/claude-sonnet-4-5"
MAX_RETRIES = 3
BACKOFF_BASE = 2.0  # seconds


class BaseAgent:
    """
    Abstract base class shared by all specialist agents.

    Manages the OpenRouter/OpenAI client, exposes a ``_call`` method with
    exponential-backoff retry, and declares the ``run`` entry-point that each
    sub-class must implement.

    Class attributes
    ----------------
    model:
        OpenRouter model identifier used for all LLM calls.
    max_tokens:
        Maximum tokens in the LLM response; overridden per sub-class.
    system_prompt:
        Default system message; overridden per sub-class.
    """

    model: str = DEFAULT_MODEL
    max_tokens: int = 4096
    system_prompt: str = "You are a helpful DevOps AI assistant."

    def __init__(self) -> None:
        """
        Initialise the OpenAI client pointed at OpenRouter.

        Raises
        ------
        EnvironmentError
            If ``OPENROUTER_API_KEY`` is not present in the environment.
        """
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENROUTER_API_KEY environment variable is not set.")
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    # ------------------------------------------------------------------
    # Core call with exponential-backoff retry
    # ------------------------------------------------------------------

    def _call(self, user_message: str, **kwargs: Any) -> str:
        """
        Send *user_message* to the LLM via OpenRouter and return the text response.

        Retries up to ``MAX_RETRIES`` times on rate-limit or connection errors
        using exponential back-off (``BACKOFF_BASE ** attempt`` seconds).

        Parameters
        ----------
        user_message:
            The user-turn content to send to the model.
        **kwargs:
            Optional overrides: ``system`` (str), ``model`` (str),
            ``max_tokens`` (int).

        Returns
        -------
        str
            Raw text content from the first choice of the LLM response.

        Raises
        ------
        openai.APIStatusError
            Re-raised immediately for 4xx/5xx responses that are not rate limits.
        RuntimeError
            When all retry attempts are exhausted.
        """
        messages = [
            {"role": "system", "content": kwargs.get("system", self.system_prompt)},
            {"role": "user", "content": user_message},
        ]

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.client.chat.completions.create(
                    model=kwargs.get("model", self.model),
                    max_tokens=kwargs.get("max_tokens", self.max_tokens),
                    messages=messages,
                )
                text = response.choices[0].message.content
                logger.debug("[%s] LLM response: %s…", self.__class__.__name__, text[:120])
                return text

            except RateLimitError as exc:
                wait = BACKOFF_BASE ** attempt
                logger.warning("Rate-limited (attempt %d/%d). Sleeping %.1fs. %s", attempt, MAX_RETRIES, wait, exc)
                time.sleep(wait)

            except APIConnectionError as exc:
                wait = BACKOFF_BASE ** attempt
                logger.warning("Connection error (attempt %d/%d). Sleeping %.1fs. %s", attempt, MAX_RETRIES, wait, exc)
                time.sleep(wait)

            except APIStatusError as exc:
                logger.error("API status error: %s", exc)
                raise

        raise RuntimeError(f"[{self.__class__.__name__}] All {MAX_RETRIES} retries exhausted.")

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def run(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        """Entry-point implemented by each sub-agent."""
        raise NotImplementedError
