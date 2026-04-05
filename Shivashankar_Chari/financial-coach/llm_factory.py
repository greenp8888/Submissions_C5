import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI


def load_environment() -> None:
    """Load environment variables from .env files."""
    load_dotenv()

    # also try loading from project root
    root_env = Path(__file__).resolve().parent.parent / ".env"
    if root_env.exists():
        load_dotenv(root_env)


def get_openrouter_client() -> OpenAI:
    """Create OpenRouter-compatible OpenAI client."""
    load_environment()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in .env")

    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )


def get_default_model() -> str:
    """Return default model name."""
    return os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")


def generate_llm_response(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 1000,
    model: Optional[str] = None,
) -> str:
    """Generate response using OpenRouter LLM."""

    client = get_openrouter_client()
    selected_model = model or get_default_model()

    response = client.chat.completions.create(
        model=selected_model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content.strip()