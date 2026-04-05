from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CostPlan:
    model_name: str
    top_k: int
    max_output_tokens: int
    prompt_tokens_est: int
    context_tokens_est: int
    estimated_total_tokens: int
    estimated_cost_usd: float
    strategy: str
    compacted_prompt: str


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def _compact_text(text: str, max_chars: int = 1200) -> str:
    if not text:
        return ""

    cleaned = " ".join(str(text).split())
    if len(cleaned) <= max_chars:
        return cleaned

    head = cleaned[: max_chars // 2].strip()
    tail = cleaned[-max_chars // 2 :].strip()
    return f"{head} ... {tail}"


def _get_model_pricing_hint(model_name: str) -> tuple[float, str]:
    name = (model_name or "").lower()

    if "gemini" in name and "flash" in name:
        return 0.0000004, "fast_low_cost"
    if "llama" in name:
        return 0.0000005, "balanced_open_model"
    if "mistral" in name:
        return 0.0000005, "balanced_open_model"
    if "qwen" in name:
        return 0.0000005, "balanced_open_model"

    return 0.0000007, "default_safe_estimate"


def build_cost_plan(model_name: str, user_prompt: str, context: str) -> CostPlan:
    compacted_prompt = _compact_text(user_prompt, max_chars=1000)
    compacted_context = _compact_text(context, max_chars=2000)

    prompt_tokens_est = _estimate_tokens(compacted_prompt)
    context_tokens_est = _estimate_tokens(compacted_context)

    total_input_tokens = prompt_tokens_est + context_tokens_est

    if total_input_tokens <= 400:
        top_k = 4
        max_output_tokens = 500
        strategy_suffix = "rich_context"
    elif total_input_tokens <= 900:
        top_k = 3
        max_output_tokens = 400
        strategy_suffix = "balanced_context"
    else:
        top_k = 2
        max_output_tokens = 300
        strategy_suffix = "compact_context"

    token_rate_usd, base_strategy = _get_model_pricing_hint(model_name)
    estimated_total_tokens = total_input_tokens + max_output_tokens
    estimated_cost_usd = round(estimated_total_tokens * token_rate_usd, 6)

    return CostPlan(
        model_name=model_name,
        top_k=top_k,
        max_output_tokens=max_output_tokens,
        prompt_tokens_est=prompt_tokens_est,
        context_tokens_est=context_tokens_est,
        estimated_total_tokens=estimated_total_tokens,
        estimated_cost_usd=estimated_cost_usd,
        strategy=f"{base_strategy}_{strategy_suffix}",
        compacted_prompt=compacted_prompt,
    )