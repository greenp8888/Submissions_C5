import os
from openai import OpenAI, AsyncOpenAI
from typing import Optional

_llm_client: Optional[OpenAI] = None
_async_llm_client: Optional[AsyncOpenAI] = None


def get_llm_client() -> OpenAI:
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
    return _llm_client


def get_async_llm_client() -> AsyncOpenAI:
    global _async_llm_client
    if _async_llm_client is None:
        _async_llm_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
    return _async_llm_client


def call_llm(prompt: str, max_tokens: int = 1024) -> str:
    """Synchronous LLM call."""
    client = get_llm_client()
    response = client.chat.completions.create(
        model="openai/gpt-4.1",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


async def call_llm_async(prompt: str, max_tokens: int = 1024) -> str:
    """Async LLM call for parallel execution."""
    client = get_async_llm_client()
    response = await client.chat.completions.create(
        model="openai/gpt-4.1",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
