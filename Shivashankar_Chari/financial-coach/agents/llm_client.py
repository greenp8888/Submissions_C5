from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
HF_CHAT_BASE_URL = "https://router.huggingface.co/v1/chat/completions"

DEFAULT_TIMEOUT_SECONDS = 60


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _extract_message_text(payload: Dict[str, Any]) -> str:
    choices = payload.get("choices", [])
    if not choices:
        return ""

    first_choice = choices[0] if isinstance(choices[0], dict) else {}
    message = first_choice.get("message", {})
    content = message.get("content", "")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(str(item.get("text", "")).strip())
        return "\n".join([part for part in text_parts if part]).strip()

    return str(content).strip()


def _extract_usage(payload: Dict[str, Any]) -> Dict[str, Any]:
    usage = payload.get("usage", {}) if isinstance(payload, dict) else {}

    return {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "estimated_prompt_tokens": None,
        "estimated_completion_tokens": None,
        "estimated_total_tokens": None,
        "source": "provider_actual" if usage else "provider_missing",
    }


def _build_system_prompt(agent_outputs: Dict[str, Any]) -> str:
    biggest_category = agent_outputs.get("biggest_category", "N/A")
    savings_rate = _safe_float(agent_outputs.get("savings_rate", 0))
    debt_status = agent_outputs.get("debt_status", "N/A")
    budget_health_score = agent_outputs.get("budget_health_score", "N/A")
    budget_health_label = agent_outputs.get("budget_health_label", "N/A")
    recurring_summary = agent_outputs.get("recurring_summary", "N/A")
    unusual_summary = agent_outputs.get("unusual_summary", "N/A")
    merchant_summary = agent_outputs.get("top_merchant_summary", "N/A")

    return f"""
You are an AI financial coach embedded in a Streamlit product.

Use only the grounded information supplied by the application.
Do not invent transactions, categories, balances, merchants, or totals.
If the prompt includes evidence labels like [R1], [R2], preserve them naturally in the answer.
Be concise, practical, and numeric where possible.
Prefer action-oriented advice over generic explanation.

Known portfolio summary:
- Biggest category: {biggest_category}
- Savings rate: {savings_rate:.1f}%
- Debt status: {debt_status}
- Budget health: {budget_health_score}/100 ({budget_health_label})
- Recurring summary: {recurring_summary}
- Unusual summary: {unusual_summary}
- Merchant summary: {merchant_summary}
""".strip()


def _build_fallback_text(
    user_prompt: str,
    agent_outputs: Dict[str, Any],
    provider_name: str,
    provider_error: Optional[str] = None,
) -> str:
    biggest_category = agent_outputs.get("biggest_category", "N/A")
    savings_rate = _safe_float(agent_outputs.get("savings_rate", 0))
    surplus = _safe_float(agent_outputs.get("surplus", 0))
    debt_status = agent_outputs.get("debt_status", "N/A")
    recurring_summary = agent_outputs.get("recurring_summary", "Recurring summary unavailable.")
    unusual_summary = agent_outputs.get("unusual_summary", "Unusual transaction summary unavailable.")
    merchant_summary = agent_outputs.get("top_merchant_summary", "Merchant summary unavailable.")
    budget_health_score = agent_outputs.get("budget_health_score", "N/A")
    budget_health_label = agent_outputs.get("budget_health_label", "N/A")

    question = _clean_text(user_prompt).lower()

    if "recurring" in question:
        core = recurring_summary
    elif "unusual" in question or "anomaly" in question:
        core = unusual_summary
    elif "merchant" in question:
        core = merchant_summary
    elif "saving" in question or "surplus" in question:
        core = (
            f"Your current estimated savings rate is {savings_rate:.1f}% "
            f"with an estimated surplus of ₹{surplus:,.0f}."
        )
    elif "debt" in question:
        core = f"Your current debt status is {debt_status}."
    else:
        core = (
            f"Your top spending category is {biggest_category}. "
            f"Budget health is {budget_health_score}/100 ({budget_health_label}). "
            f"Savings rate is {savings_rate:.1f}%."
        )

    footer = f"Provider mode: fallback after {provider_name} issue."
    if provider_error:
        footer += f" Error: {provider_error}"

    return f"{core}\n\n{footer}"


def _build_fallback_result(
    user_prompt: str,
    agent_outputs: Dict[str, Any],
    provider_name: str,
    provider_error: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "provider": provider_name,
        "text": _build_fallback_text(
            user_prompt=user_prompt,
            agent_outputs=agent_outputs,
            provider_name=provider_name,
            provider_error=provider_error,
        ),
        "usage": {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
            "estimated_prompt_tokens": None,
            "estimated_completion_tokens": None,
            "estimated_total_tokens": None,
            "source": "fallback_no_provider_usage",
        },
        "raw": None,
        "status": "fallback",
        "error": provider_error,
    }


def _post_json(url: str, headers: Dict[str, str], body: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.post(
        url,
        headers=headers,
        json=body,
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Provider returned a non-dictionary JSON payload.")

    return payload


def _call_openrouter(user_prompt: str, model_name: str, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is missing.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    referer = os.getenv("OPENROUTER_HTTP_REFERER", "").strip()
    title = os.getenv("OPENROUTER_APP_TITLE", "").strip()

    if referer:
        headers["HTTP-Referer"] = referer
    if title:
        headers["X-Title"] = title

    body = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": _build_system_prompt(agent_outputs)},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 500,
    }

    payload = _post_json(OPENROUTER_BASE_URL, headers, body)

    return {
        "provider": "OpenRouter",
        "text": _extract_message_text(payload),
        "usage": _extract_usage(payload),
        "raw": payload,
        "status": "ok",
        "error": None,
    }


def _call_huggingface(user_prompt: str, model_name: str, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.getenv("HF_TOKEN", "").strip() or os.getenv("HUGGINGFACE_API_KEY", "").strip()
    if not api_key:
        raise ValueError("HF_TOKEN or HUGGINGFACE_API_KEY is missing.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": _build_system_prompt(agent_outputs)},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 500,
    }

    payload = _post_json(HF_CHAT_BASE_URL, headers, body)

    return {
        "provider": "HuggingFace",
        "text": _extract_message_text(payload),
        "usage": _extract_usage(payload),
        "raw": payload,
        "status": "ok",
        "error": None,
    }


def is_llm_available(ai_vendor: str) -> bool:
    vendor = _clean_text(ai_vendor).lower()

    if vendor == "openrouter":
        return bool(_clean_text(os.getenv("OPENROUTER_API_KEY")))
    if vendor == "huggingface":
        return bool(_clean_text(os.getenv("HF_TOKEN")) or _clean_text(os.getenv("HUGGINGFACE_API_KEY")))

    return False


def safe_llm_response(
    user_prompt: str,
    agent_outputs: Dict[str, Any],
    ai_vendor: str,
    model_name: str,
) -> Dict[str, Any]:
    vendor = _clean_text(ai_vendor).lower()
    model = _clean_text(model_name)

    try:
        if vendor == "openrouter":
            result = _call_openrouter(
                user_prompt=user_prompt,
                model_name=model,
                agent_outputs=agent_outputs,
            )
        elif vendor == "huggingface":
            result = _call_huggingface(
                user_prompt=user_prompt,
                model_name=model,
                agent_outputs=agent_outputs,
            )
        else:
            return _build_fallback_result(
                user_prompt=user_prompt,
                agent_outputs=agent_outputs,
                provider_name=ai_vendor or "Unknown provider",
                provider_error="Unsupported provider selection.",
            )

        text = _clean_text(result.get("text"))
        if text:
            return result

        return _build_fallback_result(
            user_prompt=user_prompt,
            agent_outputs=agent_outputs,
            provider_name=result.get("provider", ai_vendor),
            provider_error="Empty response text from provider.",
        )

    except requests.exceptions.Timeout:
        return _build_fallback_result(
            user_prompt=user_prompt,
            agent_outputs=agent_outputs,
            provider_name=ai_vendor,
            provider_error="Provider request timed out.",
        )
    except requests.exceptions.HTTPError as exc:
        error_text = ""
        try:
            error_text = exc.response.text[:500] if exc.response is not None else str(exc)
        except Exception:
            error_text = str(exc)

        return _build_fallback_result(
            user_prompt=user_prompt,
            agent_outputs=agent_outputs,
            provider_name=ai_vendor,
            provider_error=f"HTTP error from provider. {error_text}",
        )
    except Exception as exc:
        return _build_fallback_result(
            user_prompt=user_prompt,
            agent_outputs=agent_outputs,
            provider_name=ai_vendor,
            provider_error=str(exc),
        )