"""
llm/openrouter.py — LLM Factory via OpenRouter

OpenRouter = a unified API gateway to 100+ LLMs.
Same interface as OpenAI SDK, different base_url.

Analogy: Think of OpenRouter as a cloud kitchen aggregator (Swiggy/Zomato).
You place one order (API call), they route it to the right kitchen (Claude/GPT/Gemini).
"""

from langchain_openai import ChatOpenAI


# Curated model options available on OpenRouter
AVAILABLE_MODELS = {
    "Claude 3.5 Haiku (Paid)":                "anthropic/claude-3.5-haiku",
    "Google Gemini Flash 2.0 (Fast)":          "google/gemini-2.0-flash-001",
    "Llama 3.2 3B (Free Tier)":                "meta-llama/llama-3.2-3b-instruct:free",
    "DeepSeek R1 (Free Tier)":                 "deepseek/deepseek-r1:free",
    "GPT-4o Mini (Balanced)":                  "openai/gpt-4o-mini",
    "Mistral 7B Instruct (Free)":              "mistralai/mistral-7b-instruct:free",
}


def get_llm(api_key: str, model: str = "anthropic/claude-3.5-haiku", temperature: float = 0.2) -> ChatOpenAI:
    """
    Initialize a ChatOpenAI-compatible LLM instance pointing at OpenRouter.

    Args:
        api_key     : Your OpenRouter API key
        model       : Model string from OpenRouter catalog
        temperature : 0.0 = deterministic, 1.0 = creative. Keep low for research tasks.

    Returns:
        Configured ChatOpenAI instance
    """
    if not api_key:
        raise ValueError("OpenRouter API key is required. Get one at openrouter.ai")

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://research-assistant.local",
            "X-Title": "Autonomous Multi-Agent Research Assistant",
        },
        temperature=temperature,
    )