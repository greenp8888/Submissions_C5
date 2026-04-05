from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

# ---------------------------------------------------------
# Optional FastMCP import
# ---------------------------------------------------------

_FASTMCP_IMPORT_ERROR: str | None = None

try:
    from mcp.server.fastmcp import FastMCP
except Exception as exc:
    FastMCP = None
    _FASTMCP_IMPORT_ERROR = str(exc)

if FastMCP is not None:
    mcp = FastMCP("financial-coach-mcp")
else:
    mcp = None


def _tool_decorator():
    """
    Returns a real MCP tool decorator when FastMCP is available,
    otherwise returns a no-op decorator so the module can still load.
    """
    if mcp is not None:
        return mcp.tool()

    def noop(func):
        return func

    return noop


tool = _tool_decorator()


# ---------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------

def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _to_dataframe(records: List[Dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


def get_mcp_runtime_status() -> Dict[str, Any]:
    return {
        "fastmcp_available": mcp is not None,
        "fastmcp_import_error": _FASTMCP_IMPORT_ERROR,
    }


# ---------------------------------------------------------
# MCP tools
# ---------------------------------------------------------

@tool
def summarize_transactions(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize uploaded financial transactions."""
    df = _to_dataframe(records)

    if df.empty:
        return {
            "source": "mcp_server",
            "tool_name": "summarize_transactions",
            "status": "empty",
            "message": "No records were provided to the MCP server.",
        }

    if "amount" not in df.columns:
        return {
            "source": "mcp_server",
            "tool_name": "summarize_transactions",
            "status": "error",
            "message": "Required column 'amount' is missing.",
        }

    df["amount"] = df["amount"].apply(_safe_float)

    expense_df = df[df["amount"] < 0].copy()
    income_df = df[df["amount"] > 0].copy()

    total_expenses = round(abs(expense_df["amount"].sum()), 2) if not expense_df.empty else 0.0
    total_credits = round(income_df["amount"].sum(), 2) if not income_df.empty else 0.0
    total_transactions = int(len(df))

    category_breakdown: Dict[str, float] = {}
    if "category" in df.columns and not expense_df.empty:
        grouped = expense_df.groupby("category")["amount"].sum().abs().sort_values(ascending=False)
        category_breakdown = {str(k): round(float(v), 2) for k, v in grouped.items()}

    top_merchant = "N/A"
    if "description" in expense_df.columns and not expense_df.empty:
        merchant_series = (
            expense_df.groupby("description")["amount"]
            .sum()
            .abs()
            .sort_values(ascending=False)
        )
        if len(merchant_series) > 0:
            top_merchant = str(merchant_series.index[0])

    return {
        "source": "mcp_server",
        "tool_name": "summarize_transactions",
        "status": "ok",
        "total_transactions": total_transactions,
        "total_expenses": total_expenses,
        "total_credits": total_credits,
        "category_breakdown": category_breakdown,
        "top_merchant": top_merchant,
        "mcp_runtime": get_mcp_runtime_status(),
    }


@tool
def analyze_debt_pressure(records: List[Dict[str, Any]], monthly_income: float) -> Dict[str, Any]:
    """Analyze debt-related outflows from transaction descriptions."""
    df = _to_dataframe(records)

    if df.empty:
        return {
            "source": "mcp_server",
            "tool_name": "analyze_debt_pressure",
            "status": "empty",
            "message": "No records were provided to the MCP server.",
        }

    if "description" not in df.columns or "amount" not in df.columns:
        return {
            "source": "mcp_server",
            "tool_name": "analyze_debt_pressure",
            "status": "error",
            "message": "Required columns 'description' and/or 'amount' are missing.",
        }

    df["amount"] = df["amount"].apply(_safe_float)

    debt_keywords = [
        "loan",
        "emi",
        "debt",
        "credit card",
        "card payment",
        "personal loan",
        "home loan",
        "auto loan",
        "consumer loan",
        "insurance payment",
    ]

    debt_df = df[
        df["description"].astype(str).str.lower().apply(
            lambda value: any(keyword in value for keyword in debt_keywords)
        )
    ].copy()

    debt_df = debt_df[debt_df["amount"] < 0].copy()

    debt_spend = round(abs(debt_df["amount"].sum()), 2) if not debt_df.empty else 0.0
    debt_count = int(len(debt_df))
    debt_ratio = round((debt_spend / monthly_income) * 100, 2) if monthly_income > 0 else 0.0

    if debt_ratio >= 40:
        debt_status = "High"
    elif debt_ratio >= 20:
        debt_status = "Moderate"
    elif debt_ratio > 0:
        debt_status = "Low"
    else:
        debt_status = "Minimal"

    return {
        "source": "mcp_server",
        "tool_name": "analyze_debt_pressure",
        "status": "ok",
        "debt_transactions_count": debt_count,
        "debt_spend": debt_spend,
        "debt_ratio": debt_ratio,
        "debt_status": debt_status,
        "mcp_runtime": get_mcp_runtime_status(),
    }


@tool
def savings_plan(records: List[Dict[str, Any]], monthly_income: float, primary_goal: str) -> Dict[str, Any]:
    """Generate a simple savings plan from expenses and income target."""
    df = _to_dataframe(records)

    if df.empty:
        return {
            "source": "mcp_server",
            "tool_name": "savings_plan",
            "status": "empty",
            "message": "No records were provided to the MCP server.",
        }

    if "amount" not in df.columns:
        return {
            "source": "mcp_server",
            "tool_name": "savings_plan",
            "status": "error",
            "message": "Required column 'amount' is missing.",
        }

    df["amount"] = df["amount"].apply(_safe_float)
    expense_df = df[df["amount"] < 0].copy()

    total_expenses = round(abs(expense_df["amount"].sum()), 2) if not expense_df.empty else 0.0
    surplus = round(monthly_income - total_expenses, 2) if monthly_income > 0 else 0.0
    savings_rate = round((surplus / monthly_income) * 100, 2) if monthly_income > 0 else 0.0
    recommended_target = round(monthly_income * 0.20, 2) if monthly_income > 0 else 0.0

    if surplus < 0:
        strategy_level = "Critical"
    elif savings_rate < 10:
        strategy_level = "Needs improvement"
    elif savings_rate < 20:
        strategy_level = "Moderate"
    else:
        strategy_level = "Strong"

    return {
        "source": "mcp_server",
        "tool_name": "savings_plan",
        "status": "ok",
        "primary_goal": primary_goal,
        "total_expenses": total_expenses,
        "surplus": surplus,
        "savings_rate": savings_rate,
        "recommended_savings_target": recommended_target,
        "strategy_level": strategy_level,
        "mcp_runtime": get_mcp_runtime_status(),
    }


if __name__ == "__main__":
    if mcp is None:
        raise RuntimeError(
            "FastMCP could not be imported. "
            f"Original import error: {_FASTMCP_IMPORT_ERROR}"
        )

    mcp.run()