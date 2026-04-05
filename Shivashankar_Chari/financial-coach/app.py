from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from agents.document_reader import (
    get_current_backend_support_message,
    get_supported_file_message,
    load_transactions,
    validate_uploaded_file,
)
from agents.expense_classifier import (
    add_categories,
    get_biggest_category,
    get_category_summary,
)
from agents.debt_analyzer import analyze_debt, format_debt_output
from agents.llm_client import is_llm_available, safe_llm_response
from agents.savings_strategist import analyze_savings, format_savings_output
from rag.retriever import retrieve_relevant_context
from rag.vector_store import build_faiss_vector_store

# Existing MCP bridge import from your current app
try:
    from utils.mcp_bridge import run_mcp_financial_probe
    MCP_BRIDGE_AVAILABLE = True
except Exception:
    run_mcp_financial_probe = None
    MCP_BRIDGE_AVAILABLE = False

# Optional architecture hooks
try:
    from orchestration.workflow import run_langgraph_financial_workflow
    LANGGRAPH_AVAILABLE = True
except Exception:
    run_langgraph_financial_workflow = None
    LANGGRAPH_AVAILABLE = False

try:
    from utils.cost_optimizer import build_cost_plan
    COST_OPTIMIZER_AVAILABLE = True
except Exception:
    build_cost_plan = None
    COST_OPTIMIZER_AVAILABLE = False


st.set_page_config(
    page_title="AI Financial Coach",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

OPENROUTER_FREE_MODELS = [
    "google/gemini-2.5-flash",
    "meta-llama/llama-3.1-8b-instruct",
    "mistralai/mistral-7b-instruct",
    "qwen/qwen2.5-7b-instruct",
]

HUGGINGFACE_FREE_MODELS = [
    "mistralai/Mistral-7B-Instruct-v0.3",
    "Qwen/Qwen2.5-7B-Instruct",
    "HuggingFaceH4/zephyr-7b-beta",
]


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

def initialize_session_state() -> None:
    defaults = {
        "transactions_df": None,
        "uploaded_file_name": None,
        "processing_error": None,
        "analysis_started": False,
        "monthly_income": 50000,
        "primary_goal": "Pay off debt faster",
        "ai_vendor": "OpenRouter",
        "model_name": "google/gemini-2.5-flash",
        "langsmith_enabled": True,
        "rag_enabled": True,
        "mcp_mode": True,
        "agent_outputs": {},
        "categorized_df": None,
        "nav_option": "My Portfolio",
        "chat_messages": [
            {
                "role": "assistant",
                "content": (
                    "Upload your bank statement and I will help analyze spending, "
                    "debt pressure, savings opportunities, recurring expenses, unusual transactions, "
                    "and evidence-backed answers."
                ),
            }
        ],
        "vector_store": None,
        "last_retrieved_context": "",
        "last_retrieved_records": [],
        "rag_status": "Not built",
        "analysis_time_seconds": 0.0,
        "rag_build_time_seconds": 0.0,
        "workflow_steps": [],
        "last_cost_plan": None,
        "workflow_engine": "LangGraph" if LANGGRAPH_AVAILABLE else "Local Workflow",
        "trace_info": {},
        "mcp_last_result": {},
        "mcp_status": "Not run",
        "provider_usage": {},
        "chat_last_citations": [],
        "last_error_log": [],
        "appearance_mode": "Dark",
        "accent_color": "Aurora",
        "email_trigger_enabled": False,
        "notification_email": "",
        "n8n_webhook_url": os.getenv("N8N_WEBHOOK_URL", "").strip(),
        "last_n8n_status": {},

        # ✅ ADD THIS LINE (FIX)
        "last_mcp_payload": {},
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def reset_uploaded_data() -> None:
    st.session_state.transactions_df = None
    st.session_state.uploaded_file_name = None
    st.session_state.processing_error = None
    st.session_state.analysis_started = False
    st.session_state.agent_outputs = {}
    st.session_state.categorized_df = None
    st.session_state.vector_store = None
    st.session_state.last_retrieved_context = ""
    st.session_state.last_retrieved_records = []
    st.session_state.rag_status = "Not built"
    st.session_state.analysis_time_seconds = 0.0
    st.session_state.rag_build_time_seconds = 0.0
    st.session_state.workflow_steps = []
    st.session_state.last_cost_plan = None
    st.session_state.trace_info = {}
    st.session_state.mcp_last_result = {}
    st.session_state.mcp_status = "Not run"
    st.session_state.provider_usage = {}
    st.session_state.chat_last_citations = []
    st.session_state.last_error_log = []
    st.session_state.last_n8n_status = {}


def log_event(message: str) -> None:
    if "last_error_log" not in st.session_state:
        st.session_state.last_error_log = []
    st.session_state.last_n8n_status = {}
    stamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.last_error_log.append(f"[{stamp}] {message}")
    st.session_state.last_error_log = st.session_state.last_error_log[-30:]


# ---------------------------------------------------------
# General helpers
# ---------------------------------------------------------

def render_metric_card(label: str, value: str) -> None:
    st.metric(label, value)


def normalize_description(text: str) -> str:
    if pd.isna(text):
        return "Unknown"
    text = str(text).strip().lower()
    text = text.replace("/", " ").replace("-", " ").replace("*", " ")
    text = " ".join(text.split())
    return text.title()


def safe_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def format_currency(value: float) -> str:
    return f"₹{value:,.0f}"


def sanitize_for_json(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    if pd.isna(value):
        return None
    return value


def dataframe_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    if df is None or df.empty:
        return []

    safe_df = df.copy()
    for col in safe_df.columns:
        if pd.api.types.is_datetime64_any_dtype(safe_df[col]):
            safe_df[col] = safe_df[col].astype(str)

    records = safe_df.to_dict(orient="records")
    cleaned_records: List[Dict[str, Any]] = []
    for row in records:
        cleaned_records.append({k: sanitize_for_json(v) for k, v in row.items()})
    return cleaned_records


def build_tool_registry() -> Dict[str, str]:
    return {
        "document_reader": "Reads and normalizes uploaded transactions",
        "expense_classifier": "Assigns categories and summarizes spending",
        "debt_analyzer": "Estimates debt pressure from transactions",
        "savings_strategist": "Computes surplus and savings posture",
        "recurring_detector": "Finds repeat merchants and likely recurring spend",
        "anomaly_detector": "Flags unusual transactions",
        "merchant_analyzer": "Ranks merchants by spend",
        "report_builder": "Combines outputs into the final summary",
        "smart_search": "Finds supporting transaction snippets for chat answers",
        "langgraph_orchestrator": "Runs stateful workflow across financial tools" if LANGGRAPH_AVAILABLE else "Fallback local orchestration",
        "cost_optimizer": "Selects prompt size, retrieval depth, and estimated token path" if COST_OPTIMIZER_AVAILABLE else "Cost optimizer unavailable",
        "mcp_client": "Calls external MCP financial tools" if MCP_BRIDGE_AVAILABLE else "MCP bridge unavailable",
    }


def detect_recurring_expenses(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    if "description" not in df.columns or "amount" not in df.columns:
        return pd.DataFrame()

    working_df = df.copy()
    working_df = working_df[working_df["amount"] < 0].copy()
    if working_df.empty:
        return pd.DataFrame()

    working_df["merchant_clean"] = working_df["description"].apply(normalize_description)
    working_df["abs_amount"] = working_df["amount"].abs().round(0)

    agg_dict = {
        "occurrences": ("merchant_clean", "size"),
        "total_spend": ("amount", lambda s: abs(s.sum())),
    }
    if "date" in working_df.columns:
        agg_dict["latest_seen"] = ("date", "max")

    recurring = (
        working_df.groupby(["merchant_clean", "abs_amount"])
        .agg(**agg_dict)
        .reset_index()
    )

    recurring = recurring[recurring["occurrences"] >= 2].copy()
    if recurring.empty:
        return recurring

    recurring = recurring.sort_values(
        ["occurrences", "total_spend"],
        ascending=[False, False],
    )

    rename_map = {
        "merchant_clean": "Merchant",
        "abs_amount": "Typical Amount",
        "occurrences": "Occurrences",
        "total_spend": "Total Spend",
        "latest_seen": "Latest Seen",
    }
    recurring = recurring.rename(columns=rename_map)

    if "Total Spend" in recurring.columns:
        recurring["Total Spend"] = recurring["Total Spend"].round(2)

    return recurring.head(15)


def detect_unusual_transactions(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty or "amount" not in df.columns:
        return pd.DataFrame()

    working_df = df.copy()
    expense_df = working_df[working_df["amount"] < 0].copy()
    if expense_df.empty:
        return pd.DataFrame()

    expense_df["abs_amount"] = expense_df["amount"].abs()

    if "category" in expense_df.columns and expense_df["category"].nunique() > 1:
        stats = (
            expense_df.groupby("category")["abs_amount"]
            .agg(["mean", "std"])
            .reset_index()
            .rename(columns={"mean": "cat_mean", "std": "cat_std"})
        )
        expense_df = expense_df.merge(stats, on="category", how="left")
        expense_df["cat_std"] = expense_df["cat_std"].fillna(0)

        expense_df["is_unusual"] = expense_df.apply(
            lambda row: row["abs_amount"] > row["cat_mean"] + (2 * row["cat_std"])
            if row["cat_std"] > 0
            else row["abs_amount"] > row["cat_mean"] * 2,
            axis=1,
        )
    else:
        overall_mean = expense_df["abs_amount"].mean()
        overall_std = expense_df["abs_amount"].std()
        if pd.isna(overall_std):
            overall_std = 0

        if overall_std > 0:
            expense_df["is_unusual"] = expense_df["abs_amount"] > overall_mean + (2 * overall_std)
        else:
            expense_df["is_unusual"] = expense_df["abs_amount"] > overall_mean * 2

    unusual_df = expense_df[expense_df["is_unusual"]].copy()

    keep_cols = [
        col for col in ["date", "description", "category", "amount", "balance"]
        if col in unusual_df.columns
    ]
    unusual_df = unusual_df[keep_cols].sort_values("amount")

    if "amount" in unusual_df.columns:
        unusual_df["amount"] = unusual_df["amount"].round(2)

    return unusual_df.head(20)


def get_top_merchants(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty or "description" not in df.columns or "amount" not in df.columns:
        return pd.DataFrame()

    working_df = df.copy()
    working_df = working_df[working_df["amount"] < 0].copy()
    if working_df.empty:
        return pd.DataFrame()

    working_df["Merchant"] = working_df["description"].apply(normalize_description)

    merchant_df = (
        working_df.groupby("Merchant")
        .agg(
            Transactions=("Merchant", "size"),
            Total_Spend=("amount", lambda s: abs(s.sum())),
        )
        .reset_index()
        .sort_values(["Total_Spend", "Transactions"], ascending=[False, False])
    )

    merchant_df["Total_Spend"] = merchant_df["Total_Spend"].round(2)
    return merchant_df.head(15)


def build_budget_health_score(
    total_expenses: float,
    monthly_income: float,
    savings_rate: float,
    debt_ratio: float,
    unusual_count: int,
) -> Tuple[int, str]:
    score = 50

    expense_ratio = total_expenses / monthly_income if monthly_income > 0 else 1.0

    if expense_ratio <= 0.60:
        score += 20
    elif expense_ratio <= 0.80:
        score += 10
    elif expense_ratio <= 1.00:
        score += 0
    else:
        score -= 20

    if savings_rate >= 25:
        score += 20
    elif savings_rate >= 15:
        score += 10
    elif savings_rate >= 5:
        score += 0
    else:
        score -= 10

    if debt_ratio <= 10:
        score += 10
    elif debt_ratio <= 20:
        score += 5
    else:
        score -= 10

    if unusual_count >= 5:
        score -= 10
    elif unusual_count >= 2:
        score -= 5

    score = max(0, min(100, int(round(score))))

    if score >= 80:
        label = "Excellent"
    elif score >= 65:
        label = "Strong"
    elif score >= 50:
        label = "Stable"
    elif score >= 35:
        label = "Needs Attention"
    else:
        label = "Critical"

    return score, label


def get_user_friendly_field_map(df: pd.DataFrame) -> pd.DataFrame:
    field_help = {
        "transaction_id": "Unique transaction reference",
        "date": "Transaction date",
        "post_date": "Date the bank posted the transaction",
        "description": "Merchant or transaction description",
        "category": "Spending category assigned by the app",
        "type": "Credit or debit indicator",
        "amount": "Transaction amount",
        "balance": "Available account balance after transaction",
        "currency": "Transaction currency",
        "account_name": "Bank account name",
        "account_type": "Type of account such as savings or checking",
    }

    rows = []
    for col in df.columns:
        rows.append(
            {
                "Field": col.replace("_", " ").title(),
                "Meaning": field_help.get(col, "Financial data field used in analysis"),
                "Format": str(df[col].dtype),
            }
        )
    return pd.DataFrame(rows)


def format_tool_output_card(title: str, content: str) -> None:
    with st.container(border=True):
        st.caption(title)
        st.write(content)


def build_quick_summary(outputs: Dict[str, Any]) -> List[str]:
    if not outputs:
        return []

    bullets = [
        f"Top spending category: {outputs.get('biggest_category', 'N/A')}",
        f"Savings rate: {outputs.get('savings_rate', 0):.1f}%",
        f"Debt status: {outputs.get('debt_status', 'N/A')}",
        f"Budget health score: {outputs.get('budget_health_score', 0)}/100",
    ]

    surplus = outputs.get("surplus", 0)
    recurring_count = outputs.get("recurring_count", 0)
    unusual_count = outputs.get("unusual_count", 0)

    if surplus < 0:
        bullets.append("Expenses are above your stated monthly income, so immediate budget correction is needed.")
    elif surplus < 10000:
        bullets.append("You still have surplus, but it is tight and should be protected.")
    else:
        bullets.append("You have usable surplus that can be split across savings, debt reduction, and reserve planning.")

    bullets.append(f"Recurring expense signals found: {recurring_count}")
    bullets.append(f"Unusual transactions flagged: {unusual_count}")

    return bullets


# ---------------------------------------------------------
# Cost optimization + usage
# ---------------------------------------------------------

def get_default_cost_plan(model_name: str, user_prompt: str, context: str) -> Dict[str, Any]:
    prompt_chars = len((user_prompt or "") + (context or ""))
    prompt_tokens_est = max(1, prompt_chars // 4)
    context_tokens_est = max(0, len(context or "") // 4)

    if "flash" in model_name.lower():
        top_k = 4
        max_output_tokens = 500
        estimated_cost_usd = round((prompt_tokens_est + context_tokens_est) * 0.0000004, 6)
        strategy = "fast_low_cost"
    else:
        top_k = 3
        max_output_tokens = 400
        estimated_cost_usd = round((prompt_tokens_est + context_tokens_est) * 0.0000007, 6)
        strategy = "balanced_quality"

    compacted_prompt = (user_prompt or "")[:300]

    return {
        "model_name": model_name,
        "top_k": top_k,
        "max_output_tokens": max_output_tokens,
        "prompt_tokens_est": prompt_tokens_est,
        "context_tokens_est": context_tokens_est,
        "estimated_total_tokens": prompt_tokens_est + context_tokens_est,
        "estimated_cost_usd": estimated_cost_usd,
        "strategy": strategy,
        "compacted_prompt": compacted_prompt,
        "usage_source": "estimated",
    }


def build_cost_plan_safe(model_name: str, user_prompt: str, context: str) -> Dict[str, Any]:
    if COST_OPTIMIZER_AVAILABLE and build_cost_plan is not None:
        try:
            plan = build_cost_plan(model_name, user_prompt, context)
            if hasattr(plan, "__dict__"):
                plan = dict(plan.__dict__)
            elif isinstance(plan, dict):
                plan = dict(plan)
            else:
                raise ValueError("Unsupported cost plan object")

            plan.setdefault("usage_source", "estimated")
            plan.setdefault("context_tokens_est", max(0, len(context or "") // 4))
            plan.setdefault("estimated_total_tokens", plan.get("prompt_tokens_est", 0) + plan.get("context_tokens_est", 0))
            plan.setdefault("compacted_prompt", (user_prompt or "")[:300])
            return plan
        except Exception as exc:
            log_event(f"Cost optimizer failed. Falling back to local estimate. {exc}")

    return get_default_cost_plan(model_name, user_prompt, context)


def extract_provider_usage(llm_result: Any, grounded_prompt: str) -> Dict[str, Any]:
    """
    Normalize usage coming from either:
    1. the new structured llm_client result dict, or
    2. a plain text fallback response.

    This keeps app.py compatible with provider-returned usage while still
    producing estimates when usage metadata is unavailable.
    """
    if isinstance(llm_result, dict):
        usage = llm_result.get("usage", {}) or {}
        response_text = str(llm_result.get("text", "") or "")
    else:
        usage = {}
        response_text = str(llm_result or "")

    prompt_tokens_est = max(1, len(grounded_prompt or "") // 4)
    completion_tokens_est = max(1, len(response_text) // 4)

    normalized = {
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "estimated_prompt_tokens": usage.get("estimated_prompt_tokens"),
        "estimated_completion_tokens": usage.get("estimated_completion_tokens"),
        "estimated_total_tokens": usage.get("estimated_total_tokens"),
        "source": usage.get("source", "estimated_only"),
    }

    if normalized["estimated_prompt_tokens"] is None:
        normalized["estimated_prompt_tokens"] = prompt_tokens_est
    if normalized["estimated_completion_tokens"] is None:
        normalized["estimated_completion_tokens"] = completion_tokens_est
    if normalized["estimated_total_tokens"] is None:
        normalized["estimated_total_tokens"] = prompt_tokens_est + completion_tokens_est

    if normalized["source"] == "provider_missing":
        normalized["source"] = "provider_missing_with_estimate"

    return normalized


# ---------------------------------------------------------
# LangSmith helpers
# ---------------------------------------------------------

def build_trace_info(stage: str, enabled: bool) -> Dict[str, Any]:
    run_id = str(uuid.uuid4())
    project = os.getenv("LANGSMITH_PROJECT", "").strip()
    endpoint = os.getenv("LANGCHAIN_ENDPOINT", "").strip() or os.getenv("LANGSMITH_ENDPOINT", "").strip()
    tracing_env = os.getenv("LANGSMITH_TRACING", "").strip().lower()

    trace_info = {
        "enabled_flag": enabled,
        "env_tracing": tracing_env in {"1", "true", "yes"},
        "run_id": run_id,
        "stage": stage,
        "project": project if project else None,
        "endpoint": endpoint if endpoint else None,
        "trace_url": None,
    }

    if trace_info["env_tracing"] and project:
        trace_info["trace_url"] = f"https://smith.langchain.com/o/default/projects/p/{project}"

    return trace_info


# ---------------------------------------------------------
# MCP helpers
# ---------------------------------------------------------

def run_mcp_tools_if_enabled(
    df: pd.DataFrame,
    monthly_income: float,
    primary_goal: str,
    mcp_mode: bool,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "enabled": mcp_mode,
        "status": "disabled",
        "source": None,
        "probe_result": None,
        "tools_called": [],
        "error": None,
    }

    if not mcp_mode:
        result["status"] = "disabled"
        return result

    if not MCP_BRIDGE_AVAILABLE or run_mcp_financial_probe is None:
        result["status"] = "bridge_unavailable"
        result["error"] = "utils.mcp_bridge.run_mcp_financial_probe import failed"
        return result

    records = dataframe_to_records(df)

    try:
        probe = run_mcp_financial_probe(
            records=records,
            monthly_income=monthly_income,
            primary_goal=primary_goal,
        )
        result["status"] = "ok"
        result["source"] = "external_mcp_probe"
        result["probe_result"] = probe
        result["tools_called"] = extract_mcp_tools_called(probe)
        return result
    except TypeError:
        # Fallback for older bridge signatures
        try:
            probe = run_mcp_financial_probe(records, monthly_income, primary_goal)
            result["status"] = "ok"
            result["source"] = "external_mcp_probe"
            result["probe_result"] = probe
            result["tools_called"] = extract_mcp_tools_called(probe)
            return result
        except Exception as exc:
            result["status"] = "failed"
            result["error"] = str(exc)
            return result
    except Exception as exc:
        result["status"] = "failed"
        result["error"] = str(exc)
        return result


def extract_mcp_tools_called(probe: Any) -> List[str]:
    if isinstance(probe, dict):
        candidates = []
        for key in ["tools_called", "tool_calls", "invocations", "executed_tools"]:
            value = probe.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        candidates.append(item)
                    elif isinstance(item, dict):
                        name = item.get("tool_name") or item.get("name")
                        if name:
                            candidates.append(str(name))
        if candidates:
            return candidates

        flat_names = []
        for key in ["summarize_transactions", "analyze_debt_pressure", "savings_plan"]:
            if key in probe:
                flat_names.append(key)
        return flat_names

    return []


def extract_mcp_tool_payload(probe: Any, tool_name: str) -> Optional[Dict[str, Any]]:
    if not isinstance(probe, dict):
        return None

    if tool_name in probe and isinstance(probe[tool_name], dict):
        return probe[tool_name]

    for key in ["tool_calls", "invocations", "executed_tools"]:
        entries = probe.get(key)
        if isinstance(entries, list):
            for item in entries:
                if isinstance(item, dict):
                    name = item.get("tool_name") or item.get("name")
                    if name == tool_name:
                        return item

    return None


# ---------------------------------------------------------
# RAG helpers
# ---------------------------------------------------------

def parse_context_blocks(context_text: str) -> List[Dict[str, str]]:
    records: List[Dict[str, str]] = []
    if not context_text:
        return records

    blocks = [block.strip() for block in context_text.split("\n\n") if block.strip()]
    for idx, block in enumerate(blocks, start=1):
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        row: Dict[str, str] = {"record_id": f"R{idx}"}
        for line in lines:
            if ":" in line:
                left, right = line.split(":", 1)
                row[left.strip().lower()] = right.strip()
            else:
                row.setdefault("title", line)
        records.append(row)
    return records


def format_retrieved_context_with_labels(context_text: str) -> Tuple[str, List[str]]:
    parsed = parse_context_blocks(context_text)
    if not parsed:
        return context_text, []

    labeled_blocks = []
    citations = []
    for row in parsed:
        record_id = row["record_id"]
        citations.append(record_id)

        parts = [f"{record_id}"]
        for key in ["date", "description", "category", "amount", "type", "balance"]:
            if key in row and row[key]:
                parts.append(f"{key.title()}: {row[key]}")
        labeled_blocks.append("\n".join(parts))

    return "\n\n".join(labeled_blocks), citations


def build_grounded_prompt(question: str, outputs: Dict[str, Any], context: str, citations: List[str]) -> str:
    citation_hint = ", ".join(citations) if citations else "No retrieved evidence IDs"

    return f"""
Answer the user's financial question using only the grounded information below.

User question:
{question}

Financial summary:
- Biggest category: {outputs.get('biggest_category', 'N/A')}
- Savings rate: {outputs.get('savings_rate', 0):.1f}%
- Debt status: {outputs.get('debt_status', 'N/A')}
- Budget health: {outputs.get('budget_health_score', 0)}/100 ({outputs.get('budget_health_label', 'N/A')})
- Recurring summary: {outputs.get('recurring_summary', 'N/A')}
- Unusual summary: {outputs.get('unusual_summary', 'N/A')}
- Top merchant summary: {outputs.get('top_merchant_summary', 'N/A')}

Retrieved transaction context:
{context}

Available evidence IDs:
{citation_hint}

Instructions:
- Be concise, practical, and numeric where possible.
- Do not invent transactions or amounts not present in the summary or retrieval context.
- If you use retrieved context, mention evidence IDs inline like [R1], [R2].
- If retrieval is empty, say that the answer is based on summary-level analysis only.
"""


def build_fallback_chat_response(
    user_prompt: str,
    outputs: Dict[str, Any],
    citations: List[str],
    rag_status_text: str,
) -> str:
    lines = []

    if "top" in user_prompt.lower() and "category" in user_prompt.lower():
        lines.append(f"Your top spending category appears to be **{outputs.get('biggest_category', 'N/A')}**.")
    elif "recurring" in user_prompt.lower():
        lines.append(outputs.get("recurring_summary", "Recurring expense summary is not available."))
    elif "unusual" in user_prompt.lower():
        lines.append(outputs.get("unusual_summary", "Unusual transaction summary is not available."))
    elif "merchant" in user_prompt.lower():
        lines.append(outputs.get("top_merchant_summary", "Merchant summary is not available."))
    elif "savings" in user_prompt.lower():
        lines.append(
            f"Your current estimated savings rate is **{outputs.get('savings_rate', 0):.1f}%**, "
            f"with an estimated surplus of **{format_currency(outputs.get('surplus', 0))}**."
        )
    else:
        lines.append(
            f"Budget health is **{outputs.get('budget_health_score', 0)}/100** "
            f"and debt status is **{outputs.get('debt_status', 'N/A')}**."
        )

    if citations:
        lines.append(f"Supporting retrieved evidence: {', '.join(f'[{c}]' for c in citations)}")
    else:
        lines.append(f"No retrieved evidence was attached. Retrieval status: {rag_status_text}")

    lines.append("This answer used fallback mode because a live LLM response was unavailable.")
    return "\n\n".join(lines)


# ---------------------------------------------------------
# Workflow execution
# ---------------------------------------------------------

def run_local_workflow(
    df: pd.DataFrame,
    monthly_income: float,
    primary_goal: str,
    ai_vendor: str,
    model_name: str,
    rag_enabled: bool,
    mcp_mode: bool,
    langsmith_enabled: bool,
) -> Dict[str, Any]:
    workflow_steps = []
    tool_registry = build_tool_registry()

    workflow_steps.append("Step 1 completed: Document Reader")
    working_df = add_categories(df)

    expense_df = working_df[working_df["amount"] < 0].copy()
    income_df = working_df[working_df["amount"] > 0].copy()

    total_expenses = abs(expense_df["amount"].sum()) if not expense_df.empty else 0
    total_credits = income_df["amount"].sum() if not income_df.empty else 0

    biggest_category = get_biggest_category(working_df)
    category_summary = get_category_summary(working_df)

    if category_summary:
        category_summary_text = " | ".join(
            [f"{cat}: ₹{amt:,.0f}" for cat, amt in category_summary.items()]
        )
    else:
        category_summary_text = "No category data available."

    workflow_steps.append("Step 2 completed: Expense Classifier")

    debt_result = analyze_debt(working_df, monthly_income)
    debt_analyzer_output = format_debt_output(debt_result)
    workflow_steps.append("Step 3 completed: Debt Analyzer")

    savings_result = analyze_savings(
        monthly_income=monthly_income,
        total_expenses=total_expenses,
        primary_goal=primary_goal,
    )
    savings_strategist_output = format_savings_output(savings_result)
    workflow_steps.append("Step 4 completed: Savings Strategist")

    recurring_df = detect_recurring_expenses(working_df)
    recurring_count = len(recurring_df)
    recurring_summary = (
        "Recurring spending signals detected across repeat merchants."
        if recurring_count > 0
        else "No strong recurring spending signals were detected."
    )
    workflow_steps.append("Step 5 completed: Recurring Detector")

    unusual_df = detect_unusual_transactions(working_df)
    unusual_count = len(unusual_df)
    unusual_summary = (
        f"{unusual_count} unusual transactions were flagged for review."
        if unusual_count > 0
        else "No unusual transactions were flagged."
    )
    workflow_steps.append("Step 6 completed: Anomaly Detector")

    merchant_df = get_top_merchants(working_df)
    top_merchant_summary = (
        f"Top merchant by spend: {merchant_df.iloc[0]['Merchant']}"
        if not merchant_df.empty
        else "Merchant-level ranking is unavailable."
    )
    workflow_steps.append("Step 7 completed: Merchant Analyzer")

    mcp_result = run_mcp_tools_if_enabled(
        df=working_df,
        monthly_income=monthly_income,
        primary_goal=primary_goal,
        mcp_mode=mcp_mode,
    )
    workflow_steps.append("Step 8 completed: MCP Probe" if mcp_result.get("status") == "ok" else "Step 8 completed: MCP Fallback")

    if mcp_result.get("status") == "ok":
        probe = mcp_result.get("probe_result") or {}

        mcp_summary_payload = extract_mcp_tool_payload(probe, "summarize_transactions") or {}
        mcp_debt_payload = extract_mcp_tool_payload(probe, "analyze_debt_pressure") or {}
        mcp_savings_payload = extract_mcp_tool_payload(probe, "savings_plan") or {}

        if isinstance(mcp_summary_payload, dict) and mcp_summary_payload.get("status") == "ok":
            total_expenses = safe_float(mcp_summary_payload.get("total_expenses", total_expenses))
            total_credits = safe_float(mcp_summary_payload.get("total_credits", total_credits))

        if isinstance(mcp_debt_payload, dict) and mcp_debt_payload.get("status") == "ok":
            debt_result["debt_spend"] = safe_float(mcp_debt_payload.get("debt_spend", debt_result["debt_spend"]))
            debt_result["debt_ratio"] = safe_float(mcp_debt_payload.get("debt_ratio", debt_result["debt_ratio"]))
            debt_result["debt_status"] = mcp_debt_payload.get("debt_status", debt_result["debt_status"])
            debt_analyzer_output = (
                f"MCP debt analysis → debt spend {format_currency(debt_result['debt_spend'])}, "
                f"debt ratio {debt_result['debt_ratio']:.1f}%, status {debt_result['debt_status']}."
            )

        if isinstance(mcp_savings_payload, dict) and mcp_savings_payload.get("status") == "ok":
            savings_result["surplus"] = safe_float(mcp_savings_payload.get("surplus", savings_result["surplus"]))
            savings_result["savings_rate"] = safe_float(mcp_savings_payload.get("savings_rate", savings_result["savings_rate"]))
            savings_result["recommended_savings_target"] = safe_float(
                mcp_savings_payload.get("recommended_savings_target", savings_result["recommended_savings_target"])
            )
            savings_result["strategy_level"] = mcp_savings_payload.get("strategy_level", savings_result["strategy_level"])
            savings_strategist_output = (
                f"MCP savings plan → surplus {format_currency(savings_result['surplus'])}, "
                f"savings rate {savings_result['savings_rate']:.1f}%, "
                f"target {format_currency(savings_result['recommended_savings_target'])}, "
                f"strategy {savings_result['strategy_level']}."
            )

    budget_health_score, budget_health_label = build_budget_health_score(
        total_expenses=total_expenses,
        monthly_income=monthly_income,
        savings_rate=savings_result["savings_rate"],
        debt_ratio=debt_result["debt_ratio"],
        unusual_count=unusual_count,
    )

    date_range_text = "N/A"
    if not working_df.empty and "date" in working_df.columns:
        min_date = working_df["date"].min()
        max_date = working_df["date"].max()
        if pd.notna(min_date) and pd.notna(max_date):
            date_range_text = f"{min_date.strftime('%d %b %Y')} to {max_date.strftime('%d %b %Y')}"

    if mcp_result.get("status") == "ok":
        mcp_status_text = f"ON | tools called: {', '.join(mcp_result.get('tools_called', [])) or 'unknown'}"
    elif mcp_result.get("status") == "disabled":
        mcp_status_text = "OFF"
    else:
        mcp_status_text = f"FAILED | {mcp_result.get('error', 'unknown error')}"

    orchestration_note = (
        f"Workflow Engine=Local Workflow | Smart Search={'ON' if rag_enabled else 'OFF'} | "
        f"MCP={'ON' if mcp_mode else 'OFF'} | MCP Status={mcp_status_text} | "
        f"LangSmith tracing flag={'ON' if langsmith_enabled else 'OFF'}"
    )

    document_reader_output = (
        f"Processed {len(working_df)} transactions successfully. "
        f"Date range: {date_range_text}. Input normalized for downstream tools."
    )

    expense_classifier_output = (
        f"Category summary → {category_summary_text}. "
        f"Biggest category: {biggest_category}."
    )

    report_builder_output = (
        f"Financial snapshot → expenses: {format_currency(total_expenses)}, "
        f"income credits in file: {format_currency(total_credits)}, "
        f"estimated surplus: {format_currency(savings_result['surplus'])}, "
        f"savings rate: {savings_result['savings_rate']:.1f}%. "
        f"Budget health: {budget_health_score}/100 ({budget_health_label}). "
        f"AI setup: {ai_vendor} using model {model_name}. {orchestration_note}"
    )
    workflow_steps.append("Step 9 completed: Report Builder")

    return {
        "categorized_df": working_df,
        "tool_registry": tool_registry,
        "workflow_steps": workflow_steps,
        "total_expenses": round(total_expenses, 2),
        "total_credits": round(total_credits, 2),
        "surplus": savings_result["surplus"],
        "savings_rate": savings_result["savings_rate"],
        "recommended_savings_target": savings_result["recommended_savings_target"],
        "savings_strategy_level": savings_result["strategy_level"],
        "biggest_category": biggest_category,
        "debt_spend": debt_result["debt_spend"],
        "debt_ratio": debt_result["debt_ratio"],
        "debt_status": debt_result["debt_status"],
        "document_reader": document_reader_output,
        "expense_classifier": expense_classifier_output,
        "debt_analyzer": debt_analyzer_output,
        "savings_strategist": savings_strategist_output,
        "report_builder": report_builder_output,
        "orchestration_note": orchestration_note,
        "recurring_df": recurring_df,
        "recurring_count": recurring_count,
        "recurring_summary": recurring_summary,
        "unusual_df": unusual_df,
        "unusual_count": unusual_count,
        "unusual_summary": unusual_summary,
        "merchant_df": merchant_df,
        "top_merchant_summary": top_merchant_summary,
        "budget_health_score": budget_health_score,
        "budget_health_label": budget_health_label,
        "workflow_engine": "Local Workflow",
        "mcp_result": mcp_result,
    }


def run_financial_workflow(
    df: pd.DataFrame,
    monthly_income: float,
    primary_goal: str,
    ai_vendor: str,
    model_name: str,
    rag_enabled: bool,
    mcp_mode: bool,
    langsmith_enabled: bool,
) -> Dict[str, Any]:
    if LANGGRAPH_AVAILABLE and run_langgraph_financial_workflow is not None:
        try:
            outputs = run_langgraph_financial_workflow(
                df=df,
                monthly_income=monthly_income,
                primary_goal=primary_goal,
                ai_vendor=ai_vendor,
                model_name=model_name,
                rag_enabled=rag_enabled,
                mcp_mode=mcp_mode,
                langsmith_enabled=langsmith_enabled,
            )
            if isinstance(outputs, dict):
                outputs.setdefault("workflow_engine", "LangGraph")
                outputs.setdefault(
                    "orchestration_note",
                    (
                        f"Workflow Engine=LangGraph | Smart Search={'ON' if rag_enabled else 'OFF'} | "
                        f"MCP={'ON' if mcp_mode else 'OFF'} | "
                        f"LangSmith tracing flag={'ON' if langsmith_enabled else 'OFF'}"
                    ),
                )

                if "mcp_result" not in outputs:
                    outputs["mcp_result"] = run_mcp_tools_if_enabled(
                        df=outputs.get("categorized_df", df),
                        monthly_income=monthly_income,
                        primary_goal=primary_goal,
                        mcp_mode=mcp_mode,
                    )
                return outputs
        except Exception as exc:
            log_event(f"LangGraph workflow failed. Switching to local workflow. {exc}")

    return run_local_workflow(
        df=df,
        monthly_income=monthly_income,
        primary_goal=primary_goal,
        ai_vendor=ai_vendor,
        model_name=model_name,
        rag_enabled=rag_enabled,
        mcp_mode=mcp_mode,
        langsmith_enabled=langsmith_enabled,
    )


# ---------------------------------------------------------
# UI renderers
# ---------------------------------------------------------


# ---------------------------------------------------------
# Theme and premium UI helpers
# ---------------------------------------------------------

def get_theme_tokens() -> Dict[str, str]:
    mode = st.session_state.get("appearance_mode", "Dark")
    accent = st.session_state.get("accent_color", "Aurora")

    accent_map = {
        "Aurora": ("#7c3aed", "#06b6d4"),
        "Emerald": ("#059669", "#14b8a6"),
        "Sunset": ("#f97316", "#ec4899"),
        "Royal": ("#2563eb", "#8b5cf6"),
    }
    primary, secondary = accent_map.get(accent, accent_map["Aurora"])

    if mode == "Light":
        return {
            "mode": mode,
            "bg": "#f5f7fb",
            "panel": "#ffffff",
            "panel_soft": "#eef4ff",
            "text": "#0f172a",
            "muted": "#475569",
            "border": "#dbe4f0",
            "shadow": "0 10px 30px rgba(15, 23, 42, 0.08)",
            "hero_text": "#ffffff",
            "primary": primary,
            "secondary": secondary,
            "badge_bg": "rgba(255,255,255,0.12)",
        }
    return {
        "mode": mode,
        "bg": "#08111f",
        "panel": "#0f172a",
        "panel_soft": "#111c34",
        "text": "#e5eefc",
        "muted": "#a7b4c9",
        "border": "#24324d",
        "shadow": "0 12px 30px rgba(2, 6, 23, 0.35)",
        "hero_text": "#ffffff",
        "primary": primary,
        "secondary": secondary,
        "badge_bg": "rgba(255,255,255,0.10)",
    }


def apply_custom_theme() -> None:
    tokens = get_theme_tokens()

    input_bg = tokens["panel"]
    input_text = tokens["text"]
    input_border = tokens["border"]
    soft_bg = tokens["panel_soft"]

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: radial-gradient(circle at top left, {tokens['panel_soft']} 0%, {tokens['bg']} 35%, {tokens['bg']} 100%);
            color: {tokens['text']};
        }}

        [data-testid="stAppViewContainer"] {{
            background: radial-gradient(circle at top left, {tokens['panel_soft']} 0%, {tokens['bg']} 35%, {tokens['bg']} 100%);
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {tokens['panel']} 0%, {tokens['panel_soft']} 100%);
            border-right: 1px solid {tokens['border']};
        }}

        [data-testid="stSidebar"] * {{
            color: {tokens['text']};
        }}

        .block-container {{
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }}

        /* Metric cards */
        div[data-testid="stMetric"] {{
            background: linear-gradient(135deg, {tokens['panel']} 0%, {tokens['panel_soft']} 100%);
            border: 1px solid {tokens['border']};
            border-radius: 18px;
            padding: 14px 16px;
            box-shadow: {tokens['shadow']};
        }}

        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] div {{
            color: {tokens['text']} !important;
        }}

        /* Generic containers */
        .nova-section-card {{
            background: linear-gradient(180deg, {tokens['panel']} 0%, {tokens['panel_soft']} 100%);
            border: 1px solid {tokens['border']};
            border-radius: 20px;
            padding: 18px 18px 12px 18px;
            box-shadow: {tokens['shadow']};
            margin-bottom: 1rem;
        }}

        /* Inputs */
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"] > div,
        .stNumberInput div[data-baseweb="input"] > div,
        .stTextInput div[data-baseweb="input"] > div,
        .stTextArea textarea {{
            background: {input_bg} !important;
            color: {input_text} !important;
            border: 1px solid {input_border} !important;
            border-radius: 14px !important;
        }}

        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea {{
            color: {input_text} !important;
            background: transparent !important;
        }}

        .stSelectbox label,
        .stTextInput label,
        .stNumberInput label,
        .stRadio label,
        .stFileUploader label,
        .stTextArea label {{
            color: {tokens['text']} !important;
        }}

        /* File uploader */
        [data-testid="stFileUploader"] {{
            background: linear-gradient(180deg, {tokens['panel']} 0%, {tokens['panel_soft']} 100%);
            border: 1px solid {tokens['border']};
            border-radius: 16px;
            padding: 0.4rem;
        }}

        [data-testid="stFileUploader"] section {{
            background: transparent !important;
            color: {tokens['text']} !important;
        }}

        /* Radio group */
        .stRadio > div {{
            background: transparent !important;
            color: {tokens['text']} !important;
        }}

        /* Buttons */
        .stButton > button, .stDownloadButton > button {{
            border-radius: 14px !important;
            border: 1px solid {tokens['border']} !important;
            box-shadow: {tokens['shadow']};
            background: linear-gradient(120deg, {tokens['primary']} 0%, {tokens['secondary']} 100%) !important;
            color: white !important;
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.45rem;
        }}

        .stTabs [data-baseweb="tab"] {{
            border-radius: 999px;
            padding-left: 0.9rem;
            padding-right: 0.9rem;
            background: {soft_bg} !important;
            color: {tokens['text']} !important;
            border: 1px solid {tokens['border']} !important;
        }}

        /* Expanders */
        details {{
            background: linear-gradient(180deg, {tokens['panel']} 0%, {tokens['panel_soft']} 100%);
            border: 1px solid {tokens['border']};
            border-radius: 16px;
            padding: 0.2rem 0.6rem;
        }}

        details summary {{
            color: {tokens['text']} !important;
        }}

        /* Tables / dataframes */
        [data-testid="stDataFrame"] {{
            border: 1px solid {tokens['border']};
            border-radius: 16px;
            overflow: hidden;
        }}

        /* Hero */
        .nova-hero {{
            background: linear-gradient(120deg, {tokens['primary']} 0%, {tokens['secondary']} 100%);
            border-radius: 24px;
            padding: 24px 28px;
            color: {tokens['hero_text']};
            box-shadow: {tokens['shadow']};
            margin-bottom: 1rem;
        }}

        .nova-hero h1 {{
            margin: 0 0 0.35rem 0;
            font-size: 2rem;
            line-height: 1.15;
        }}

        .nova-hero p {{
            margin: 0;
            color: rgba(255,255,255,0.92);
            font-size: 1rem;
        }}

        .nova-badge-wrap {{
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-top: 0.85rem;
        }}

        .nova-badge {{
            background: {tokens['badge_bg']};
            border: 1px solid rgba(255,255,255,0.18);
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            font-size: 0.85rem;
            color: {tokens['hero_text']};
        }}

        .nova-step {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.8rem 0.9rem;
            background: {soft_bg};
            border: 1px solid {tokens['border']};
            border-radius: 14px;
            margin-bottom: 0.65rem;
            color: {tokens['text']};
        }}

        .nova-step-icon {{
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(120deg, {tokens['primary']} 0%, {tokens['secondary']} 100%);
            color: white;
            font-weight: 700;
        }}

        .nova-chip {{
            display: inline-block;
            padding: 0.3rem 0.65rem;
            border-radius: 999px;
            background: {soft_bg};
            border: 1px solid {tokens['border']};
            color: {tokens['text']};
            margin: 0.15rem 0.35rem 0.15rem 0;
            font-size: 0.83rem;
        }}

        .nova-subtle {{
            color: {tokens['muted']};
            font-size: 0.95rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_runtime_observability():
    st.subheader("⚙️ Runtime & Observability")

    with st.expander("View Execution Details", expanded=False):

        col1, col2 = st.columns(2)

        # LEFT SIDE
        with col1:
            st.markdown("### 🔗 MCP Status")
            render_mcp_status_panel()

            st.markdown("### 📡 LangSmith Trace")
            render_trace_info()

        # RIGHT SIDE
        with col2:
            st.markdown("### 💰 Token Usage")
            render_provider_usage()

            st.markdown("### ⚠️ Error Logs")

            if st.session_state.last_error_log:
                for row in st.session_state.last_error_log[-10:]:
                    st.code(row)
            else:
                st.info("No runtime issues logged.")



def render_hero(title: str, subtitle: str) -> None:
    badges = [
        f"Mode: {st.session_state.get('appearance_mode', 'Dark')}",
        f"Workflow: {st.session_state.get('workflow_engine', 'Local Workflow')}",
        f"RAG: {'On' if st.session_state.get('rag_enabled') else 'Off'}",
        f"MCP: {'On' if st.session_state.get('mcp_mode') else 'Off'}",
        f"Trace: {'On' if st.session_state.get('langsmith_enabled') else 'Off'}",
    ]
    badge_html = "".join([f"<span class='nova-badge'>{badge}</span>" for badge in badges])
    st.markdown(
        f"""
        <div class="nova-hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
            <div class="nova-badge-wrap">{badge_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_ai_execution_pipeline(outputs: Dict[str, Any]) -> None:
    steps = [
        "Document Ingestion",
        "Expense Classification",
        "Debt Analysis",
        "Savings Strategy",
        "Recurring Pattern Detection",
        "Anomaly Detection",
        "Merchant Insights",
        "MCP Financial Tool Execution" if st.session_state.mcp_mode else "Local Financial Logic",
        "Final Report Generation",
    ]
    st.markdown('<div class="nova-section-card">', unsafe_allow_html=True)
    st.subheader("AI Execution Pipeline")
    st.markdown(
        f"""
        <div class="nova-subtle">
        Transparent execution path across workflow orchestration, retrieval grounding, financial tools, and LLM reasoning.
        </div>
        """,
        unsafe_allow_html=True,
    )
    chips = [
        f"Engine: {outputs.get('workflow_engine', st.session_state.workflow_engine)}",
        f"Smart Search: {'Enabled' if st.session_state.rag_enabled else 'Disabled'}",
        f"MCP: {'Enabled' if st.session_state.mcp_mode else 'Disabled'}",
        f"Tracing: {'Enabled' if st.session_state.langsmith_enabled else 'Disabled'}",
    ]
    st.markdown("".join([f"<span class='nova-chip'>{chip}</span>" for chip in chips]), unsafe_allow_html=True)
    for idx, step in enumerate(steps, start=1):
        st.markdown(
            f"""
            <div class="nova-step">
                <span class="nova-step-icon">{idx}</span>
                <div><strong>{step}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def send_n8n_analysis_email(outputs: Dict[str, Any]) -> Dict[str, Any]:
    webhook_url = (st.session_state.get("n8n_webhook_url") or "").strip()
    recipient = (st.session_state.get("notification_email") or "").strip()

    if not webhook_url:
        return {
            "status": "skipped",
            "message": "N8N_WEBHOOK_URL is not configured.",
            "recipient": recipient or None,
        }

    payload = {
        "trigger_source": "streamlit_financial_coach",
        "channel": "email",
        "recipient_email": recipient,
        "file_name": st.session_state.get("uploaded_file_name"),
        "analysis_time_seconds": round(float(st.session_state.get("analysis_time_seconds", 0.0)), 2),
        "workflow_engine": outputs.get("workflow_engine", st.session_state.get("workflow_engine")),
        "summary": {
            "total_credits": outputs.get("total_credits"),
            "total_expenses": outputs.get("total_expenses"),
            "surplus": outputs.get("surplus"),
            "savings_rate": outputs.get("savings_rate"),
            "debt_status": outputs.get("debt_status"),
            "budget_health_score": outputs.get("budget_health_score"),
            "budget_health_label": outputs.get("budget_health_label"),
            "biggest_category": outputs.get("biggest_category"),
            "recurring_summary": outputs.get("recurring_summary"),
            "unusual_summary": outputs.get("unusual_summary"),
            "report_builder": outputs.get("report_builder"),
        },
        "mcp_status": st.session_state.get("mcp_status"),
        "rag_status": st.session_state.get("rag_status"),
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=20)
        response.raise_for_status()
        try:
            response_body = response.json()
        except Exception:
            response_body = response.text[:500]
        return {
            "status": "sent",
            "message": "n8n webhook accepted the analysis payload.",
            "recipient": recipient or None,
            "http_status": response.status_code,
            "response": response_body,
        }
    except Exception as exc:
        return {
            "status": "failed",
            "message": str(exc),
            "recipient": recipient or None,
        }


def render_visual_analytics(df: pd.DataFrame) -> None:
    if df is None or df.empty:
        st.info("No data available for charts yet.")
        return

    expense_df = df[df["amount"] < 0].copy()
    income_df = df[df["amount"] > 0].copy()

    chart_tab1, chart_tab2, chart_tab3, chart_tab4, chart_tab5 = st.tabs(
        ["Category Mix", "Top Categories", "Spending Trend", "Credit vs Debit", "Monthly Trend"]
    )

    with chart_tab1:
        if not expense_df.empty and "category" in expense_df.columns:
            category_spend = (
                expense_df.groupby("category")["amount"]
                .sum()
                .abs()
                .reset_index()
                .sort_values("amount", ascending=False)
            )
            fig_pie = px.pie(
                category_spend,
                names="category",
                values="amount",
                title="Spending Distribution by Category",
                hole=0.35,
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expense category data available for this chart.")

    with chart_tab2:
        if not expense_df.empty and "category" in expense_df.columns:
            category_spend = (
                expense_df.groupby("category")["amount"]
                .sum()
                .abs()
                .reset_index()
                .sort_values("amount", ascending=False)
            )
            fig_bar = px.bar(
                category_spend.head(10),
                x="category",
                y="amount",
                title="Top Spending Categories",
                text="amount",
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No expense category data available for this chart.")

    with chart_tab3:
        if "date" in df.columns:
            trend_df = df.copy().sort_values("date")
            trend_df["expense_only"] = trend_df["amount"].apply(lambda x: abs(x) if x < 0 else 0)
            daily_spend = (
                trend_df.groupby("date")["expense_only"]
                .sum()
                .reset_index()
                .sort_values("date")
            )
            fig_line = px.line(
                daily_spend,
                x="date",
                y="expense_only",
                title="Daily Spending Trend",
                markers=True,
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Date column unavailable for trend view.")

    with chart_tab4:
        total_credit = income_df["amount"].sum() if not income_df.empty else 0
        total_debit = abs(expense_df["amount"].sum()) if not expense_df.empty else 0
        fig_cd = px.pie(
            names=["Credit", "Debit"],
            values=[total_credit, total_debit],
            title="Credit vs Debit Distribution",
            hole=0.35,
        )
        st.plotly_chart(fig_cd, use_container_width=True)

    with chart_tab5:
        if "date" in df.columns:
            monthly_df = df.copy()
            monthly_df["month"] = pd.to_datetime(monthly_df["date"]).dt.to_period("M").astype(str)
            monthly_df["expense_only"] = monthly_df["amount"].apply(lambda x: abs(x) if x < 0 else 0)
            monthly_grouped = (
                monthly_df.groupby("month")["expense_only"]
                .sum()
                .reset_index()
                .sort_values("month")
            )
            fig_month = px.bar(
                monthly_grouped,
                x="month",
                y="expense_only",
                title="Monthly Spending Trend",
                text="expense_only",
            )
            st.plotly_chart(fig_month, use_container_width=True)
        else:
            st.info("Date column unavailable for monthly trend.")


def render_recurring_section(recurring_df: pd.DataFrame) -> None:
    st.subheader("Recurring Expenses")
    if recurring_df is None or recurring_df.empty:
        st.info("No strong recurring expense pattern was detected.")
    else:
        st.dataframe(recurring_df, use_container_width=True, height=300)


def render_unusual_section(unusual_df: pd.DataFrame) -> None:
    st.subheader("Unusual Transactions")
    if unusual_df is None or unusual_df.empty:
        st.info("No unusual transactions were flagged.")
    else:
        st.dataframe(unusual_df, use_container_width=True, height=300)


def render_merchant_section(merchant_df: pd.DataFrame) -> None:
    st.subheader("Top Merchants")
    if merchant_df is None or merchant_df.empty:
        st.info("Merchant-level insights are not available.")
    else:
        st.dataframe(merchant_df, use_container_width=True, height=300)


def render_smart_context_as_cards(context_text: str) -> None:
    if not context_text:
        st.info("Ask a question in Chat with AI to see the exact supporting transaction context here.")
        return

    blocks = [block.strip() for block in context_text.split("\n\n") if block.strip()]
    for idx, block in enumerate(blocks, start=1):
        with st.container(border=True):
            lines = [line.strip() for line in block.split("\n") if line.strip()]
            if not lines:
                continue

            st.markdown(f"**Evidence R{idx}**")
            for line in lines[:6]:
                st.write(line)

            if len(lines) > 6:
                with st.expander("View full retrieved record"):
                    st.text("\n".join(lines[6:]))


def render_provider_usage() -> None:
    usage = st.session_state.provider_usage
    if not usage:
        st.info("No chat usage data yet.")
        return

    with st.container(border=True):
        st.subheader("Token Usage Observability")
        rows = [
            ["Prompt tokens", usage.get("prompt_tokens")],
            ["Completion tokens", usage.get("completion_tokens")],
            ["Total tokens", usage.get("total_tokens")],
            ["Estimated prompt tokens", usage.get("estimated_prompt_tokens")],
            ["Estimated completion tokens", usage.get("estimated_completion_tokens")],
            ["Estimated total tokens", usage.get("estimated_total_tokens")],
            ["Usage source", usage.get("source")],
        ]
        usage_df = pd.DataFrame(rows, columns=["Metric", "Value"])
        st.dataframe(usage_df, use_container_width=True, hide_index=True)
        if usage.get("source") == "provider_actual":
            st.caption("These token counts came from the provider payload.")
        else:
            st.caption("Provider token counts were unavailable for this response, so estimated values are also shown.")


def render_trace_info() -> None:
    trace = st.session_state.trace_info
    if not trace:
        st.info("No trace metadata available yet.")
        return

    with st.container(border=True):
        st.subheader("LangSmith Trace Metadata")
        st.write(f"Run ID: `{trace.get('run_id', 'N/A')}`")
        st.write(f"Stage: `{trace.get('stage', 'N/A')}`")
        st.write(f"Tracing flag enabled: `{trace.get('enabled_flag', False)}`")
        st.write(f"Tracing env active: `{trace.get('env_tracing', False)}`")
        st.write(f"Project: `{trace.get('project', 'N/A')}`")
        if trace.get("trace_url"):
            st.markdown(f"[Open LangSmith Project]({trace['trace_url']})")
        else:
            st.caption("Trace URL not available because LANGSMITH_TRACING or LANGSMITH_PROJECT is not fully configured.")


def render_mcp_status_panel() -> None:
    mcp_result = st.session_state.mcp_last_result
    if not mcp_result:
        st.info("MCP has not been executed yet.")
        return

    with st.container(border=True):
        st.subheader("MCP Runtime Proof")
        st.write(f"Status: **{mcp_result.get('status', 'unknown')}**")
        st.write(f"Source: **{mcp_result.get('source', 'N/A')}**")
        st.write(f"Tools called: **{', '.join(mcp_result.get('tools_called', [])) or 'None detected'}**")
        if mcp_result.get("error"):
            st.error(mcp_result["error"])

        probe = mcp_result.get("probe_result")
        if probe is not None:
            with st.expander("View raw MCP probe payload", expanded=False):
                st.json(probe)



def render_sidebar() -> None:
    outputs = st.session_state.agent_outputs

    st.markdown("## Financial Command Center")
    if st.session_state.uploaded_file_name:
        st.success(f"Connected to {st.session_state.uploaded_file_name}")
    else:
        st.info("Upload a structured statement to activate analysis")

    st.divider()

    st.markdown("## Navigation")
    st.session_state.nav_option = st.radio(
        "",
        ["My Portfolio", "Deep Research", "Chat with AI"],
        index=["My Portfolio", "Deep Research", "Chat with AI"].index(st.session_state.nav_option),
        label_visibility="collapsed",
    )

    st.divider()

    st.divider()

    if st.button("Clear Analysis", use_container_width=True):
        reset_uploaded_data()
        st.rerun()

    with st.expander("Appearance", expanded=True):
        selected_mode = st.radio(
        "Theme",
        ["Dark", "Light"],
        index=["Dark", "Light"].index(st.session_state.appearance_mode),
        horizontal=True,
        key="appearance_mode_radio",
    )

    selected_accent = st.selectbox(
        "Accent palette",
        ["Aurora", "Emerald", "Sunset", "Royal"],
        index=["Aurora", "Emerald", "Sunset", "Royal"].index(st.session_state.accent_color),
        key="accent_color_select",
    )

    theme_changed = False

    if selected_mode != st.session_state.appearance_mode:
        st.session_state.appearance_mode = selected_mode
        theme_changed = True

    if selected_accent != st.session_state.accent_color:
        st.session_state.accent_color = selected_accent
        theme_changed = True

    if theme_changed:
        st.rerun()

    with st.expander("AI Settings", expanded=False):
        ai_vendor = st.selectbox(
            "AI Vendor",
            ["OpenRouter", "HuggingFace", "Local / Offline (Coming Soon)"],
            index=["OpenRouter", "HuggingFace", "Local / Offline (Coming Soon)"].index(
                st.session_state.ai_vendor
                if st.session_state.ai_vendor in ["OpenRouter", "HuggingFace", "Local / Offline (Coming Soon)"]
                else "OpenRouter"
            ),
        )
        st.session_state.ai_vendor = ai_vendor

        if ai_vendor == "OpenRouter":
            model_name = st.selectbox(
                "Model name",
                OPENROUTER_FREE_MODELS,
                index=OPENROUTER_FREE_MODELS.index(st.session_state.model_name)
                if st.session_state.model_name in OPENROUTER_FREE_MODELS
                else 0,
            )
        elif ai_vendor == "HuggingFace":
            model_name = st.selectbox(
                "Model name",
                HUGGINGFACE_FREE_MODELS,
                index=0,
            )
        else:
            model_name = st.text_input("Model name", value="local-model-placeholder")

        st.session_state.model_name = model_name
        st.session_state.langsmith_enabled = st.checkbox(
            "Enable LangSmith tracing",
            value=st.session_state.langsmith_enabled,
        )
        st.session_state.rag_enabled = st.checkbox(
            "Enable Smart Search (RAG)",
            value=st.session_state.rag_enabled,
        )
        st.session_state.mcp_mode = st.checkbox(
            "Enable external MCP financial probe",
            value=st.session_state.mcp_mode,
        )

        if LANGGRAPH_AVAILABLE:
            st.success("LangGraph workflow is available.")
        else:
            st.info("LangGraph import not available. Using local workflow fallback.")

        if COST_OPTIMIZER_AVAILABLE:
            st.success("Cost optimizer is available.")
        else:
            st.info("Cost optimizer import not available. Using fallback cost estimation.")

        if MCP_BRIDGE_AVAILABLE:
            st.success("MCP bridge import is available.")
        else:
            st.warning("MCP bridge import is not available. MCP will not execute.")

    with st.expander("Automation and Email", expanded=False):
        st.session_state.email_trigger_enabled = st.checkbox(
            "Trigger n8n email after analysis",
            value=st.session_state.email_trigger_enabled,
        )
        st.session_state.notification_email = st.text_input(
            "Recipient email",
            value=st.session_state.notification_email,
            placeholder="name@example.com",
        )
        st.session_state.n8n_webhook_url = st.text_input(
            "n8n webhook URL",
            value=st.session_state.n8n_webhook_url,
            type="password",
            help="This webhook can forward the analysis to n8n, which can then send an email.",
        )
        if st.session_state.last_n8n_status:
            st.write(st.session_state.last_n8n_status)

    with st.expander("Available Tools", expanded=False):
        tool_registry = build_tool_registry()
        for tool_name, desc in tool_registry.items():
            st.markdown(f"- **{tool_name}**: {desc}")

    st.divider()
    st.caption(get_supported_file_message())
    st.caption(get_current_backend_support_message())



def render_upload_panel() -> None:
    st.markdown('<div class="nova-section-card">', unsafe_allow_html=True)
    st.subheader("Portfolio Input")
    st.caption("For the current demo, use one structured statement file at a time.")

    uploaded_file = st.file_uploader(
        "Bank statement or expense file",
        type=["csv", "xlsx", "xls"],
        help="Current demo mode supports structured files only: CSV, XLSX, XLS.",
    )

    if uploaded_file is not None:
        is_valid, validation_message = validate_uploaded_file(uploaded_file)
        if not is_valid:
            st.session_state.processing_error = validation_message
            st.session_state.transactions_df = None
            st.session_state.uploaded_file_name = uploaded_file.name
        else:
            try:
                transactions_df = load_transactions(uploaded_file)
                st.session_state.transactions_df = transactions_df
                st.session_state.uploaded_file_name = uploaded_file.name
                st.session_state.processing_error = None
                st.success(f"{uploaded_file.name} uploaded successfully.")
            except Exception as exc:
                st.session_state.transactions_df = None
                st.session_state.uploaded_file_name = uploaded_file.name
                st.session_state.processing_error = str(exc)
                log_event(f"File load failed: {exc}")

    monthly_income = st.number_input(
        "Monthly income (₹)",
        min_value=0,
        value=int(st.session_state.monthly_income),
        step=1000,
    )
    st.session_state.monthly_income = monthly_income

    primary_goal = st.selectbox(
        "Primary goal",
        [
            "Pay off debt faster",
            "Increase monthly savings",
            "Reduce overspending",
            "Build emergency fund",
            "Improve budget discipline",
        ],
        index=[
            "Pay off debt faster",
            "Increase monthly savings",
            "Reduce overspending",
            "Build emergency fund",
            "Improve budget discipline",
        ].index(st.session_state.primary_goal),
    )
    st.session_state.primary_goal = primary_goal

    analyze_clicked = st.button("Analyze Portfolio", type="primary", use_container_width=True)

    if st.session_state.processing_error:
        st.error(st.session_state.processing_error)

    if analyze_clicked:
        if st.session_state.transactions_df is None:
            st.warning("Please upload a valid CSV or Excel file first.")
        else:
            st.session_state.analysis_started = True

            try:
                start_time = time.time()
                st.session_state.trace_info = build_trace_info(
                    stage="portfolio_analysis",
                    enabled=st.session_state.langsmith_enabled,
                )

                with st.spinner("Running workflow, building retrieval context, scoring financial health, and probing MCP..."):
                    outputs = run_financial_workflow(
                        df=st.session_state.transactions_df,
                        monthly_income=st.session_state.monthly_income,
                        primary_goal=st.session_state.primary_goal,
                        ai_vendor=st.session_state.ai_vendor,
                        model_name=st.session_state.model_name,
                        rag_enabled=st.session_state.rag_enabled,
                        mcp_mode=st.session_state.mcp_mode,
                        langsmith_enabled=st.session_state.langsmith_enabled,
                    )

                    st.session_state.agent_outputs = outputs
                    st.session_state.categorized_df = outputs.get("categorized_df")
                    st.session_state.workflow_steps = outputs.get("workflow_steps", [])
                    st.session_state.workflow_engine = outputs.get("workflow_engine", st.session_state.workflow_engine)
                    st.session_state.mcp_last_result = outputs.get("mcp_result", {})
                    st.session_state.mcp_status = outputs.get("mcp_result", {}).get("status", "Not run")

                    rag_start = time.time()
                    if st.session_state.rag_enabled and outputs.get("categorized_df") is not None:
                        try:
                            st.session_state.vector_store = build_faiss_vector_store(outputs["categorized_df"])
                            st.session_state.rag_status = "Ready"
                        except Exception as rag_exc:
                            st.session_state.vector_store = None
                            st.session_state.rag_status = f"Failed: {rag_exc}"
                            log_event(f"RAG build failed: {rag_exc}")
                    else:
                        st.session_state.vector_store = None
                        st.session_state.rag_status = "Disabled"

                    st.session_state.rag_build_time_seconds = time.time() - rag_start
                    st.session_state.analysis_time_seconds = time.time() - start_time

                    if st.session_state.email_trigger_enabled:
                        st.session_state.last_n8n_status = send_n8n_analysis_email(outputs)
                    else:
                        st.session_state.last_n8n_status = {
                            "status": "idle",
                            "message": "n8n email trigger is disabled.",
                        }

                st.success("Analysis completed successfully.")
                if st.session_state.last_n8n_status.get("status") == "sent":
                    st.success("Analysis payload was sent to n8n for downstream email delivery.")
                elif st.session_state.email_trigger_enabled and st.session_state.last_n8n_status.get("status") != "sent":
                    st.warning(f"n8n trigger status: {st.session_state.last_n8n_status.get('message', 'Unknown issue')}")

            except Exception as exc:
                st.session_state.agent_outputs = {}
                st.session_state.categorized_df = None
                st.session_state.vector_store = None
                st.session_state.rag_status = "Failed"
                st.session_state.mcp_status = "Failed"
                log_event(f"Analysis failed: {exc}")
                st.error(f"Analysis failed: {exc}")

    st.markdown("</div>", unsafe_allow_html=True)



def render_portfolio_view() -> None:

    # -------------------------------
    # HERO
    # -------------------------------
    render_hero(
        "💰 AI Financial Intelligence Dashboard",
        "Agentic AI • MCP • RAG • Real-time insights • Automation ready",
    )

    # -------------------------------
    # MAIN SPLIT LAYOUT
    # -------------------------------
    left_panel, right_panel = st.columns([0.9, 1.8], gap="large")

    # -------------------------------
    # LEFT PANEL → INPUTS
    # -------------------------------
    with left_panel:
        st.markdown("### 📥 Portfolio Input")
        render_upload_panel()

    # -------------------------------
    # RIGHT PANEL → DASHBOARD
    # -------------------------------
    with right_panel:

        outputs = st.session_state.agent_outputs

        if not (st.session_state.analysis_started and outputs):
            st.info("Upload a file and run analysis to unlock insights.")
            return

        # -------------------------------
        # KPI ROW
        # -------------------------------
        credits = float(outputs.get("total_credits", 0) or 0)
        expenses = float(outputs.get("total_expenses", 0) or 0)
        actual_surplus = credits - expenses

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("💰 Credits", format_currency(credits))
        col2.metric("💸 Expenses", format_currency(expenses))
        col3.metric("📊 Surplus", format_currency(actual_surplus))
        col4.metric("📈 Savings", f"{outputs.get('savings_rate', 0):.1f}%")
        col5.metric("🧠 Health", f"{outputs.get('budget_health_score', 0)}/100")

        st.markdown("---")

        # -------------------------------
        # GRID → CHART + INSIGHTS
        # -------------------------------
        grid_left, grid_right = st.columns([1.5, 1])

        # LEFT → CHARTS
        with grid_left:
            st.subheader("📊 Financial Trends")
            render_visual_analytics(st.session_state.categorized_df)

        # RIGHT → INSIGHTS
        with grid_right:
            st.subheader("🧠 AI Insights")

            for item in build_quick_summary(outputs):
                st.markdown(f"• {item}")

            st.markdown("---")

            st.markdown("### ⚡ Key Signals")
            st.markdown(outputs.get("recurring_summary", ""))
            st.markdown(outputs.get("unusual_summary", ""))
            st.markdown(outputs.get("top_merchant_summary", ""))

        st.markdown("---")

        # -------------------------------
        # PIPELINE
        # -------------------------------
        render_ai_execution_pipeline(outputs)

        st.markdown("---")

        # -------------------------------
        # AGENT OUTPUTS
        # -------------------------------
        st.subheader("⚙️ Agent Outputs")

        with st.expander("📄 Document Reader"):
            st.write(outputs.get("document_reader"))

        with st.expander("🏷️ Expense Classifier"):
            st.write(outputs.get("expense_classifier"))

        with st.expander("💳 Debt Analyzer"):
            st.write(outputs.get("debt_analyzer"))

        with st.expander("📈 Savings Strategist"):
            st.write(outputs.get("savings_strategist"))

        with st.expander("📊 Final Report"):
            st.write(outputs.get("report_builder"))

        st.markdown("---")

        # -------------------------------
        # MCP STATUS
        # -------------------------------
        st.subheader("🔗 MCP Execution")

        mcp_result = outputs.get("mcp_result", {})

        if mcp_result.get("status") == "ok":
            st.success(f"✅ MCP executed | Tools: {', '.join(mcp_result.get('tools_called', []))}")
        elif mcp_result.get("status") == "failed":
            st.error("❌ MCP failed")
        else:
            st.info("ℹ️ MCP not active")

        st.markdown("---")

        # -------------------------------
        # EMAIL AUTOMATION
        # -------------------------------
        st.subheader("📧 Automation")

        if st.checkbox("Send report via email (n8n)", key="email_trigger_enabled"):
            st.text_input("Recipient Email", key="notification_email")

            if st.button("Send Email"):
                result = send_n8n_analysis_email(outputs)
                st.session_state.last_n8n_status = result

        if st.session_state.last_n8n_status:
            status = st.session_state.last_n8n_status

            if status.get("status") == "sent":
                st.success("📧 Email sent successfully")
            elif status.get("status") == "failed":
                st.warning(f"⚠️ Email failed: {status.get('message')}")

        st.markdown("---")
        render_runtime_observability()
            



def render_runtime_observability():
    st.subheader("⚙️ Runtime & Observability")

    with st.expander("View Execution Details", expanded=False):

        col1, col2 = st.columns(2)

        # -------------------------------
        # LEFT → MCP + LangSmith
        # -------------------------------
        with col1:
            st.markdown("### 🔗 MCP Status")
            render_mcp_status_panel()

            st.markdown("### 📡 LangSmith Trace")
            render_trace_info()

        # -------------------------------
        # RIGHT → Tokens + Errors
        # -------------------------------
        with col2:
            st.markdown("### 💰 Token Usage")
            render_provider_usage()

            st.markdown("### ⚠️ Error Logs")

            if st.session_state.last_error_log:
                for row in st.session_state.last_error_log[-10:]:
                    st.code(row)
            else:
                st.info("No runtime issues logged.")

        # -------------------------------
        # OPTIONAL MCP PAYLOAD
        # -------------------------------
        if st.session_state.last_mcp_payload:
            st.markdown("### 🧾 MCP Raw Payload")
            st.json(st.session_state.last_mcp_payload)



def render_deep_research_view() -> None:
    render_hero(
        "Deep Research",
        "Structured view of extracted data, workflow evidence, retrieval context, runtime traces, and MCP execution details.",
    )

    outputs = st.session_state.agent_outputs
    if not outputs:
        st.info("Run portfolio analysis first to activate deep research.")
        return

    # ✅ FIXED KPI CALCULATION
    credits = float(outputs.get("total_credits", 0) or 0)
    expenses = float(outputs.get("total_expenses", 0) or 0)
    actual_surplus = credits - expenses

    metric_cols = st.columns(5)
    metrics = [
        ("Credits", f"₹{credits:,.0f}"),
        ("Expenses", f"₹{expenses:,.0f}"),
        ("Surplus", f"₹{actual_surplus:,.0f}"),
        ("Savings Rate", f"{outputs.get('savings_rate', 0):.1f}%"),
        ("Budget Health", f"{outputs.get('budget_health_score', 0)}/100"),
    ]
    for col, (label, value) in zip(metric_cols, metrics):
        with col:
            st.metric(label, value)

    # --- rest remains unchanged ---

    with st.container(border=True):
        st.subheader("Research Summary")
        for item in build_quick_summary(outputs):
            st.markdown(f"- {item}")

    render_ai_execution_pipeline(outputs)

    with st.container(border=True):
        st.subheader("Agent Outputs")
        for key in [
            "document_reader",
            "expense_classifier",
            "debt_analyzer",
            "savings_strategist",
            "recurring_summary",
            "unusual_summary",
            "top_merchant_summary",
            "report_builder",
        ]:
            st.write(f"**{key}**: {outputs.get(key, 'N/A')}")

    with st.container(border=True):
        st.subheader("Retrieved Context Preview")
        if st.session_state.last_retrieved_context:
            st.code(st.session_state.last_retrieved_context)
        else:
            st.info("Ask a question in Chat with AI to populate the retrieval context.")

    with st.container(border=True):
        st.subheader("MCP + Trace Metadata")
        st.json(
            {
                "mcp_status": st.session_state.mcp_status,
                "mcp_last_result": st.session_state.mcp_last_result,
                "trace_info": st.session_state.trace_info,
                "provider_usage": st.session_state.provider_usage,
                "n8n_status": st.session_state.last_n8n_status,
            }
        )

    with st.container(border=True):
        st.subheader("Data Tables")
        if outputs.get("categorized_df") is not None:
            st.dataframe(outputs.get("categorized_df"), use_container_width=True)
        if outputs.get("merchant_df") is not None and not outputs["merchant_df"].empty:
            st.dataframe(outputs["merchant_df"], use_container_width=True)
        if outputs.get("unusual_df") is not None and not outputs["unusual_df"].empty:
            st.dataframe(outputs["unusual_df"], use_container_width=True)



def render_chat_view() -> None:
    render_hero(
        "Chat with AI",
        "Ask grounded financial questions using analyzed data, Smart Search retrieval, evidence labels, and provider-observed token usage.",
    )

    outputs = st.session_state.agent_outputs

    if not outputs:
        st.info("Run portfolio analysis first, then chat with your data.")
        return

    status_col1, status_col2, status_col3 = st.columns(3)
    with status_col1:
        if is_llm_available(st.session_state.ai_vendor):
            st.success("Live AI chat is enabled.")
        else:
            st.info("Live AI chat is not configured. The app will use a fallback response.")
    with status_col2:
        st.info(f"Workflow: {st.session_state.workflow_engine}")
    with status_col3:
        st.info(f"RAG status: {st.session_state.rag_status}")

    with st.expander("Suggested questions", expanded=False):
        for q in [
            "What are my top three spending categories?",
            "Do I have any recurring expenses?",
            "Which transactions look unusual?",
            "How can I improve my savings next month?",
            "Which merchants take most of my money?",
        ]:
            st.markdown(f"- {q}")

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input("Ask about spending, debt, savings, merchants, or unusual transactions")
    if not user_prompt:
        return

    st.session_state.trace_info = build_trace_info(
        stage="chat",
        enabled=st.session_state.langsmith_enabled,
    )

    st.session_state.chat_messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    raw_context = ""
    formatted_context = ""
    citations: List[str] = []

    preview_plan = build_cost_plan_safe(st.session_state.model_name, user_prompt, "")

    if st.session_state.vector_store is not None and st.session_state.rag_enabled:
        try:
            top_k = int(preview_plan.get("top_k", 3))
            raw_context = retrieve_relevant_context(st.session_state.vector_store, user_prompt, top_k=top_k)
            st.session_state.last_retrieved_context = raw_context
            formatted_context, citations = format_retrieved_context_with_labels(raw_context)
            st.session_state.chat_last_citations = citations
        except Exception as exc:
            raw_context = ""
            formatted_context = ""
            citations = []
            st.session_state.last_retrieved_context = ""
            log_event(f"Retrieval failed during chat: {exc}")

    final_plan = build_cost_plan_safe(st.session_state.model_name, user_prompt, formatted_context)
    st.session_state.last_cost_plan = final_plan

    grounded_prompt = build_grounded_prompt(user_prompt, outputs, formatted_context, citations)

    with st.chat_message("assistant"):
        with st.expander("Cost optimization snapshot", expanded=False):
            st.json(st.session_state.last_cost_plan)

        if citations:
            st.caption(f"Evidence attached: {', '.join(f'[{c}]' for c in citations)}")
        else:
            st.caption("No retrieved evidence attached for this answer.")

        if is_llm_available(st.session_state.ai_vendor):
            try:
                llm_result = safe_llm_response(
                    user_prompt=grounded_prompt,
                    agent_outputs=outputs,
                    ai_vendor=st.session_state.ai_vendor,
                    model_name=st.session_state.model_name,
                )
            except Exception as exc:
                log_event(f"LLM call failed. Using fallback answer. {exc}")
                llm_result = {
                    "provider": st.session_state.ai_vendor,
                    "text": build_fallback_chat_response(
                        user_prompt=user_prompt,
                        outputs=outputs,
                        citations=citations,
                        rag_status_text=st.session_state.rag_status,
                    ),
                    "usage": {},
                    "raw": None,
                    "status": "fallback_exception",
                    "error": str(exc),
                }
        else:
            llm_result = {
                "provider": st.session_state.ai_vendor,
                "text": build_fallback_chat_response(
                    user_prompt=user_prompt,
                    outputs=outputs,
                    citations=citations,
                    rag_status_text=st.session_state.rag_status,
                ),
                "usage": {},
                "raw": None,
                "status": "fallback_no_provider",
                "error": None,
            }

        response_text = str(llm_result.get("text", "") or "").strip()
        if not response_text:
            response_text = build_fallback_chat_response(
                user_prompt=user_prompt,
                outputs=outputs,
                citations=citations,
                rag_status_text=st.session_state.rag_status,
            )

        usage = extract_provider_usage(llm_result, grounded_prompt)
        st.session_state.provider_usage = usage

        if citations and "[R" not in response_text:
            response_text = f"{response_text}\n\nSupporting evidence: {', '.join(f'[{c}]' for c in citations)}"

        provider_name = llm_result.get("provider", st.session_state.ai_vendor)
        response_status = llm_result.get("status", "unknown")
        response_error = llm_result.get("error")

        st.markdown(response_text)

        with st.expander("LLM response diagnostics", expanded=False):
            st.write(f"Provider: **{provider_name}**")
            st.write(f"Status: **{response_status}**")
            if response_error:
                st.caption(f"Error: {response_error}")

            raw_payload = llm_result.get("raw")
            if raw_payload is not None:
                st.json(raw_payload)

    st.session_state.chat_messages.append({"role": "assistant", "content": response_text})


def main() -> None:
    initialize_session_state()
    apply_custom_theme()

    with st.sidebar:
        render_sidebar()

        st.markdown("---")
        st.markdown("### 📌 Session Summary")
        st.markdown(f"""
- File: {st.session_state.get("uploaded_file_name", "None")}
- Workflow: {st.session_state.get("workflow_engine", "Local Workflow")}
- RAG: {'ON' if st.session_state.get("rag_enabled") else 'OFF'}
- MCP: {'ON' if st.session_state.get("mcp_mode") else 'OFF'}
""")

    if st.session_state.nav_option == "My Portfolio":
        render_portfolio_view()
    elif st.session_state.nav_option == "Deep Research":
        render_deep_research_view()
    else:
        render_chat_view()

    

def render_main_dashboard(outputs: Dict[str, Any]):
    # -------------------------------
    # HERO (ONLY ONCE)
    # -------------------------------
    render_hero(
        "AI Financial Intelligence Dashboard",
        "Agentic AI + MCP + RAG powered financial insights"
    )

    # -------------------------------
    # SEARCH BAR (ZENI STYLE)
    # -------------------------------
    st.markdown("""
    <div style="
        background: rgba(255,255,255,0.05);
        padding: 14px;
        border-radius: 14px;
        margin-bottom: 20px;
        border: 1px solid rgba(255,255,255,0.08);
        font-size: 14px;
    ">
    🔍 Try searching for account, merchant, payee, transaction...
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------
    # KPI ROW
    # -------------------------------
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("💰 Net Income", format_currency(outputs.get("total_credits", 0)))
    col2.metric("💸 Expenses", format_currency(outputs.get("total_expenses", 0)))
    col3.metric("📊 Surplus", format_currency(outputs.get("surplus", 0)))
    col4.metric("📈 Savings", f"{outputs.get('savings_rate', 0):.1f}%")
    col5.metric("🧠 Health", f"{outputs.get('budget_health_score', 0)}/100")

    st.markdown("---")

    # -------------------------------
    # MAIN GRID
    # -------------------------------
    left, right = st.columns([1.4, 1])

    # LEFT → CHARTS
    with left:
        st.subheader("📊 Financial Trends")
        render_visual_analytics(outputs.get("categorized_df"))

    # RIGHT → INSIGHTS
    with right:
        st.subheader("🧠 AI Insights")

        for bullet in build_quick_summary(outputs):
            st.markdown(f"• {bullet}")

        st.markdown("---")

        st.markdown("### ⚡ Key Signals")
        st.markdown(outputs.get("recurring_summary", ""))
        st.markdown(outputs.get("unusual_summary", ""))
        st.markdown(outputs.get("top_merchant_summary", ""))

    st.markdown("---")

    # -------------------------------
    # PIPELINE
    # -------------------------------
    render_ai_execution_pipeline(outputs)

    st.markdown("---")

    # -------------------------------
    # AGENT OUTPUTS (EXPANDABLE)
    # -------------------------------
    st.subheader("⚙️ Agent Outputs")

    with st.expander("📄 Document Reader"):
        st.write(outputs.get("document_reader"))

    with st.expander("🏷️ Expense Classifier"):
        st.write(outputs.get("expense_classifier"))

    with st.expander("💳 Debt Analyzer"):
        st.write(outputs.get("debt_analyzer"))

    with st.expander("📈 Savings Strategist"):
        st.write(outputs.get("savings_strategist"))

    with st.expander("📊 Final Report"):
        st.write(outputs.get("report_builder"))

    st.markdown("---")

    # -------------------------------
    # MCP STATUS
    # -------------------------------
    st.subheader("🔗 MCP Execution")

    mcp_result = outputs.get("mcp_result", {})

    if mcp_result.get("status") == "ok":
        st.success(f"✅ MCP executed | Tools: {', '.join(mcp_result.get('tools_called', []))}")
    elif mcp_result.get("status") == "failed":
        st.error("❌ MCP failed")
    else:
        st.info("ℹ️ MCP not active")

    # -------------------------------
    # EMAIL
    # -------------------------------
    if st.checkbox("📧 Send report via email"):
        if st.button("Send Email"):
            result = send_n8n_analysis_email(outputs)
            if result["status"] == "sent":
                st.success("Email sent successfully")
            else:
                st.error("Email failed")


if __name__ == "__main__":
    main()