import os
from typing import Optional

from openai import OpenAI


def get_api_key(ai_vendor: str) -> Optional[str]:
    """Return API key based on selected vendor."""
    vendor = (ai_vendor or "").strip().lower()

    if vendor == "openrouter":
        return os.getenv("OPENROUTER_API_KEY")

    if vendor == "huggingface":
        return os.getenv("HUGGINGFACE_API_KEY")

    return os.getenv("OPENROUTER_API_KEY")


def get_base_url(ai_vendor: str) -> str:
    """Return API base URL for selected vendor."""
    vendor = (ai_vendor or "").strip().lower()

    if vendor == "openrouter":
        return "https://openrouter.ai/api/v1"

    return "https://openrouter.ai/api/v1"


def is_llm_available(ai_vendor: str) -> bool:
    """Check whether LLM credentials are available."""
    return bool(get_api_key(ai_vendor))


def build_financial_context(agent_outputs: dict) -> str:
    """Build compact structured context for LLM prompts."""
    if not agent_outputs:
        return "No analyzed financial context is available yet."

    return f"""
Financial Summary
- Total credits: ₹{agent_outputs.get("total_credits", 0):,.0f}
- Total expenses: ₹{agent_outputs.get("total_expenses", 0):,.0f}
- Surplus: ₹{agent_outputs.get("surplus", 0):,.0f}
- Savings rate: {agent_outputs.get("savings_rate", 0):.1f}%
- Biggest spending category: {agent_outputs.get("biggest_category", "N/A")}
- Debt status: {agent_outputs.get("debt_status", "N/A")}
- Debt ratio: {agent_outputs.get("debt_ratio", 0):.1f}%
- Savings strategy level: {agent_outputs.get("savings_strategy_level", "N/A")}

Agent Notes
- Expense classifier: {agent_outputs.get("expense_classifier", "N/A")}
- Debt analyzer: {agent_outputs.get("debt_analyzer", "N/A")}
- Savings strategist: {agent_outputs.get("savings_strategist", "N/A")}
- Report builder: {agent_outputs.get("report_builder", "N/A")}
""".strip()


def ask_llm(
    user_prompt: str,
    agent_outputs: dict,
    ai_vendor: str,
    model_name: str,
) -> str:
    """Call LLM with financial context and return response."""
    api_key = get_api_key(ai_vendor)
    if not api_key:
        raise ValueError(
            f"No API key found for {ai_vendor}. Please set the required environment variable."
        )

    client = OpenAI(
        api_key=api_key,
        base_url=get_base_url(ai_vendor),
    )

    system_prompt = """
You are an AI financial coach for a hackathon demo.

Rules:
- Be practical, concise, and specific.
- Use only the provided financial context.
- Do not invent transactions or numbers.
- Give action-oriented advice.
- Keep responses under 180 words.
- When relevant, mention spending category, debt pressure, savings rate, and next best action.
""".strip()

    financial_context = build_financial_context(agent_outputs)

    completion = client.chat.completions.create(
        model=model_name,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"{financial_context}\n\nUser question: {user_prompt}",
            },
        ],
    )

    return completion.choices[0].message.content.strip()


def safe_llm_response(
    user_prompt: str,
    agent_outputs: dict,
    ai_vendor: str,
    model_name: str,
) -> str:
    """Return LLM response with graceful fallback."""
    try:
        return ask_llm(
            user_prompt=user_prompt,
            agent_outputs=agent_outputs,
            ai_vendor=ai_vendor,
            model_name=model_name,
        )
    except Exception as exc:
        return (
            "Live LLM response is unavailable right now. "
            f"Reason: {exc}"
        )
