from typing import Dict, Any

import pandas as pd


def analyze_debt(
    df: pd.DataFrame,
    monthly_income: float,
) -> Dict[str, Any]:
    """Analyze debt pressure using transaction descriptions and monthly income"""
    if df is None or df.empty:
        return {
            "debt_transactions_count": 0,
            "debt_spend": 0.0,
            "debt_ratio": 0.0,
            "debt_status": "No data",
            "debt_message": "No transaction data available for debt analysis.",
        }

    working_df = df.copy()

    if "description" not in working_df.columns or "amount" not in working_df.columns:
        return {
            "debt_transactions_count": 0,
            "debt_spend": 0.0,
            "debt_ratio": 0.0,
            "debt_status": "Insufficient data",
            "debt_message": "Required columns for debt analysis are missing.",
        }

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
    ]

    debt_df = working_df[
        working_df["description"].astype(str).str.lower().apply(
            lambda value: any(keyword in value for keyword in debt_keywords)
        )
    ].copy()

    debt_df = debt_df[debt_df["amount"] < 0].copy()

    debt_spend = abs(debt_df["amount"].sum()) if not debt_df.empty else 0.0
    debt_transactions_count = int(len(debt_df))

    if monthly_income > 0:
        debt_ratio = round((debt_spend / monthly_income) * 100, 1)
    else:
        debt_ratio = 0.0

    if debt_ratio >= 40:
        debt_status = "High"
    elif debt_ratio >= 20:
        debt_status = "Moderate"
    elif debt_ratio > 0:
        debt_status = "Low"
    else:
        debt_status = "Minimal"

    if monthly_income <= 0:
        debt_message = (
            "Monthly income is zero or unavailable, so debt pressure cannot be estimated reliably."
        )
    elif debt_transactions_count == 0:
        debt_message = (
            "No explicit debt or EMI transactions were detected in the uploaded data. "
            "Debt pressure appears minimal based on transaction descriptions."
        )
    else:
        debt_message = (
            f"Detected {debt_transactions_count} debt-related transactions with estimated "
            f"monthly debt outflow of ₹{debt_spend:,.0f}. Debt-to-income pressure is "
            f"{debt_ratio:.1f}%, which falls in the {debt_status.lower()} range."
        )

    return {
        "debt_transactions_count": debt_transactions_count,
        "debt_spend": round(debt_spend, 2),
        "debt_ratio": debt_ratio,
        "debt_status": debt_status,
        "debt_message": debt_message,
    }


def format_debt_output(debt_result: Dict[str, Any]) -> str:
    """Format debt analysis result into app-friendly text"""
    if not debt_result:
        return "Debt analysis is unavailable."

    return debt_result.get("debt_message", "Debt analysis is unavailable.")
