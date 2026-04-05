import os
from openai import APIStatusError, AsyncOpenAI, AuthenticationError, OpenAI
from typing import Optional

_llm_client: Optional[OpenAI] = None
_async_llm_client: Optional[AsyncOpenAI] = None


def _openrouter_key_help() -> None:
    print(
        "\n"
        + "=" * 72
        + "\n"
        "OpenRouter API key issue (401 / User not found).\n"
        "  • Create a key: https://openrouter.ai/keys\n"
        "  • In backend/.env set: OPENROUTER_API_KEY=sk-or-v1-... (no quotes)\n"
        "  • Add credits if the key is new: https://openrouter.ai/credits\n"
        "  • Restart uvicorn after changing .env\n"
        + "=" * 72
        + "\n"
    )


def _is_openrouter_auth_error(exc: BaseException) -> bool:
    code = getattr(exc, "status_code", None)
    if code == 401:
        return True
    s = str(exc).lower()
    return "401" in s and ("user not found" in s or "unauthorized" in s or "invalid" in s)


def get_llm_client() -> OpenAI:
    global _llm_client
    if _llm_client is None:
        key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
        if not key:
            print("⚠️  OPENROUTER_API_KEY is missing or empty in backend/.env — LLM calls will fail.")
        elif key.startswith("sk-or-v1-xxxxx") or "xxxxxxxx" in key:
            print("⚠️  OPENROUTER_API_KEY still looks like a placeholder — replace it with your real key.")
        _llm_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=key or None,
        )
    return _llm_client


def get_async_llm_client() -> AsyncOpenAI:
    global _async_llm_client
    if _async_llm_client is None:
        key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
        _async_llm_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=key or None,
        )
    return _async_llm_client


def call_llm(prompt: str, max_tokens: int = 1024) -> str:
    """Synchronous LLM call."""
    client = get_llm_client()
    try:
        response = client.chat.completions.create(
            model="openai/gpt-4.1",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""
    except (APIStatusError, AuthenticationError) as e:
        if _is_openrouter_auth_error(e):
            _openrouter_key_help()
        raise
    except Exception as e:
        if _is_openrouter_auth_error(e):
            _openrouter_key_help()
        raise


async def call_llm_async(
    prompt: str,
    max_tokens: int = 1024,
    *,
    temperature: Optional[float] = None,
) -> str:
    """Async LLM call for parallel execution."""
    client = get_async_llm_client()
    kwargs: dict = {
        "model": "openai/gpt-4.1",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    try:
        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""
    except (APIStatusError, AuthenticationError) as e:
        if _is_openrouter_auth_error(e):
            _openrouter_key_help()
        raise
    except Exception as e:
        if _is_openrouter_auth_error(e):
            _openrouter_key_help()
        raise
