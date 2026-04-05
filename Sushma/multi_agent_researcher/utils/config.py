"""Configuration loader for the Multi-Agent Researcher.

Loads OpenRouter, Tavily, and SerpAPI credentials from environment
variables. Mirrors the pattern used in browser_automation_agent.
"""

import os

from dotenv import load_dotenv


def load_config() -> dict[str, str | None]:
    """Load configuration from environment variables.

    Reads from a .env file in the working directory (via python-dotenv)
    and returns a dict of all relevant settings.

    Returns:
        dict[str, str | None]: Configuration dictionary with keys:
            - openrouter_api_key: OpenRouter API key for LLM orchestration.
            - openrouter_base_url: OpenRouter API endpoint URL.
            - model_name: Model identifier to use via OpenRouter.
            - tavily_api_key: Tavily API key for web search (required).
            - serpapi_api_key: SerpAPI key for Google Search (optional).
    """
    load_dotenv()
    return {
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY"),
        "openrouter_base_url": os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ),
        "model_name": os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini"),
        "tavily_api_key": os.getenv("TAVILY_API_KEY"),
        "serpapi_api_key": os.getenv("SERPAPI_API_KEY"),
    }
