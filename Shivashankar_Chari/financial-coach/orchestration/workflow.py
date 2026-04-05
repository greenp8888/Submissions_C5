from __future__ import annotations

from typing import Any, Dict, TypedDict

import pandas as pd

from agents.debt_analyzer import analyze_debt, format_debt_output
from agents.expense_classifier import add_categories, get_biggest_category, get_category_summary
from agents.savings_strategist import analyze_savings, format_savings_output


class FinancialWorkflowState(TypedDict, total=False):
    df: pd.DataFrame
    monthly_income: float
    primary_goal: str
    ai_vendor: str
    model_name: str
    rag_enabled: bool
    mcp_mode: bool
    langsmith_enabled: bool

    categorized_df: pd.DataFrame
    total_expenses: float
    total_credits: float
    biggest_category: str
    category_summary_text: str

    debt_result: Dict[str, Any]
    debt_analyzer_output: str

    savings_result: Dict[str, Any]
    savings_strategist_output: str

    recurring_df: pd.DataFrame
    recurring_count: int
    recurring_summary: str

    unusual_df: pd.DataFrame
    unusual_count: int
    unusual_summary: str

    merchant_df: pd.DataFrame
    top_merchant_summary: str

    budget_health_score: int
    budget_health_label: str

    document_reader_output: str
    expense_classifier_output: str
    report_builder_output: str
    orchestration_note: str
    workflow_steps: list[str]
    workflow_engine: str


# ---------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------

def normalize_description(text: Any) -> str:
    if pd.isna(text):
        return "Unknown"
    text = str(text).strip().lower()
    text = text.replace("/", " ").replace("-", " ").replace("*", " ")
    text = " ".join(text.split())
    return text.title()


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

    recurring = recurring.rename(
        columns={
            "merchant_clean": "Merchant",
            "abs_amount": "Typical Amount",
            "occurrences": "Occurrences",
            "total_spend": "Total Spend",
            "latest_seen": "Latest Seen",
        }
    )

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
) -> tuple[int, str]:
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


# ---------------------------------------------------------
# Workflow nodes
# ---------------------------------------------------------

def node_document_reader(state: FinancialWorkflowState) -> FinancialWorkflowState:
    df = state["df"].copy()
    workflow_steps = list(state.get("workflow_steps", []))
    workflow_steps.append("Step 1 completed: Document Reader")

    date_range_text = "N/A"
    if not df.empty and "date" in df.columns:
        min_date = df["date"].min()
        max_date = df["date"].max()
        if pd.notna(min_date) and pd.notna(max_date):
            try:
                date_range_text = f"{min_date.strftime('%d %b %Y')} to {max_date.strftime('%d %b %Y')}"
            except Exception:
                date_range_text = f"{min_date} to {max_date}"

    state["document_reader_output"] = (
        f"Processed {len(df)} transactions successfully. "
        f"Date range: {date_range_text}. Input normalized for downstream tools."
    )
    state["workflow_steps"] = workflow_steps
    return state


def node_expense_classifier(state: FinancialWorkflowState) -> FinancialWorkflowState:
    df = state["df"]
    categorized_df = add_categories(df)

    expense_df = categorized_df[categorized_df["amount"] < 0].copy()
    income_df = categorized_df[categorized_df["amount"] > 0].copy()

    total_expenses = abs(expense_df["amount"].sum()) if not expense_df.empty else 0.0
    total_credits = income_df["amount"].sum() if not income_df.empty else 0.0

    biggest_category = get_biggest_category(categorized_df)
    category_summary = get_category_summary(categorized_df)

    if category_summary:
        category_summary_text = " | ".join(
            [f"{cat}: ₹{amt:,.0f}" for cat, amt in category_summary.items()]
        )
    else:
        category_summary_text = "No category data available."

    workflow_steps = list(state.get("workflow_steps", []))
    workflow_steps.append("Step 2 completed: Expense Classifier")

    state["categorized_df"] = categorized_df
    state["total_expenses"] = round(total_expenses, 2)
    state["total_credits"] = round(total_credits, 2)
    state["biggest_category"] = biggest_category
    state["category_summary_text"] = category_summary_text
    state["expense_classifier_output"] = (
        f"Category summary → {category_summary_text}. Biggest category: {biggest_category}."
    )
    state["workflow_steps"] = workflow_steps
    return state


def node_debt_analyzer(state: FinancialWorkflowState) -> FinancialWorkflowState:
    categorized_df = state["categorized_df"]
    monthly_income = state["monthly_income"]

    debt_result = analyze_debt(categorized_df, monthly_income)
    debt_analyzer_output = format_debt_output(debt_result)

    workflow_steps = list(state.get("workflow_steps", []))
    workflow_steps.append("Step 3 completed: Debt Analyzer")

    state["debt_result"] = debt_result
    state["debt_analyzer_output"] = debt_analyzer_output
    state["workflow_steps"] = workflow_steps
    return state


def node_savings_strategist(state: FinancialWorkflowState) -> FinancialWorkflowState:
    total_expenses = state["total_expenses"]
    monthly_income = state["monthly_income"]
    primary_goal = state["primary_goal"]

    savings_result = analyze_savings(
        monthly_income=monthly_income,
        total_expenses=total_expenses,
        primary_goal=primary_goal,
    )
    savings_strategist_output = format_savings_output(savings_result)

    workflow_steps = list(state.get("workflow_steps", []))
    workflow_steps.append("Step 4 completed: Savings Strategist")

    state["savings_result"] = savings_result
    state["savings_strategist_output"] = savings_strategist_output
    state["workflow_steps"] = workflow_steps
    return state


def node_recurring_detector(state: FinancialWorkflowState) -> FinancialWorkflowState:
    categorized_df = state["categorized_df"]
    recurring_df = detect_recurring_expenses(categorized_df)
    recurring_count = len(recurring_df)

    recurring_summary = (
        "Recurring spending signals detected across repeat merchants."
        if recurring_count > 0
        else "No strong recurring spending signals were detected."
    )

    workflow_steps = list(state.get("workflow_steps", []))
    workflow_steps.append("Step 5 completed: Recurring Detector")

    state["recurring_df"] = recurring_df
    state["recurring_count"] = recurring_count
    state["recurring_summary"] = recurring_summary
    state["workflow_steps"] = workflow_steps
    return state


def node_anomaly_detector(state: FinancialWorkflowState) -> FinancialWorkflowState:
    categorized_df = state["categorized_df"]
    unusual_df = detect_unusual_transactions(categorized_df)
    unusual_count = len(unusual_df)

    unusual_summary = (
        f"{unusual_count} unusual transactions were flagged for review."
        if unusual_count > 0
        else "No unusual transactions were flagged."
    )

    workflow_steps = list(state.get("workflow_steps", []))
    workflow_steps.append("Step 6 completed: Anomaly Detector")

    state["unusual_df"] = unusual_df
    state["unusual_count"] = unusual_count
    state["unusual_summary"] = unusual_summary
    state["workflow_steps"] = workflow_steps
    return state


def node_merchant_analyzer(state: FinancialWorkflowState) -> FinancialWorkflowState:
    categorized_df = state["categorized_df"]
    merchant_df = get_top_merchants(categorized_df)

    top_merchant_summary = (
        f"Top merchant by spend: {merchant_df.iloc[0]['Merchant']}"
        if not merchant_df.empty
        else "Merchant-level ranking is unavailable."
    )

    workflow_steps = list(state.get("workflow_steps", []))
    workflow_steps.append("Step 7 completed: Merchant Analyzer")

    state["merchant_df"] = merchant_df
    state["top_merchant_summary"] = top_merchant_summary
    state["workflow_steps"] = workflow_steps
    return state


def node_report_builder(state: FinancialWorkflowState) -> FinancialWorkflowState:
    total_expenses = state["total_expenses"]
    total_credits = state["total_credits"]
    savings_result = state["savings_result"]
    debt_result = state["debt_result"]
    unusual_count = state["unusual_count"]

    budget_health_score, budget_health_label = build_budget_health_score(
        total_expenses=total_expenses,
        monthly_income=state["monthly_income"],
        savings_rate=savings_result["savings_rate"],
        debt_ratio=debt_result["debt_ratio"],
        unusual_count=unusual_count,
    )

    orchestration_note = (
        f"Workflow Engine=LangGraph | Smart Search={'ON' if state['rag_enabled'] else 'OFF'} | "
        f"MCP={'ON' if state['mcp_mode'] else 'OFF'} | "
        f"LangSmith tracing flag={'ON' if state['langsmith_enabled'] else 'OFF'}"
    )

    report_builder_output = (
        f"Financial snapshot → expenses: ₹{total_expenses:,.0f}, income credits in file: ₹{total_credits:,.0f}, "
        f"estimated surplus: ₹{savings_result['surplus']:,.0f}, savings rate: {savings_result['savings_rate']:.1f}%. "
        f"Budget health: {budget_health_score}/100 ({budget_health_label}). "
        f"AI setup: {state['ai_vendor']} using model {state['model_name']}. {orchestration_note}"
    )

    workflow_steps = list(state.get("workflow_steps", []))
    workflow_steps.append("Step 8 completed: Report Builder")

    state["budget_health_score"] = budget_health_score
    state["budget_health_label"] = budget_health_label
    state["orchestration_note"] = orchestration_note
    state["report_builder_output"] = report_builder_output
    state["workflow_steps"] = workflow_steps
    state["workflow_engine"] = "LangGraph"
    return state


# ---------------------------------------------------------
# Public runner
# ---------------------------------------------------------

def run_langgraph_financial_workflow(
    df: pd.DataFrame,
    monthly_income: float,
    primary_goal: str,
    ai_vendor: str,
    model_name: str,
    rag_enabled: bool,
    mcp_mode: bool,
    langsmith_enabled: bool,
) -> Dict[str, Any]:
    """
    Lightweight LangGraph-style workflow runner.

    If you later want to wire the actual langgraph.StateGraph package, this function
    can be upgraded without changing app.py.
    """

    state: FinancialWorkflowState = {
        "df": df.copy(),
        "monthly_income": float(monthly_income),
        "primary_goal": primary_goal,
        "ai_vendor": ai_vendor,
        "model_name": model_name,
        "rag_enabled": rag_enabled,
        "mcp_mode": mcp_mode,
        "langsmith_enabled": langsmith_enabled,
        "workflow_steps": [],
        "workflow_engine": "LangGraph",
    }

    state = node_document_reader(state)
    state = node_expense_classifier(state)
    state = node_debt_analyzer(state)
    state = node_savings_strategist(state)
    state = node_recurring_detector(state)
    state = node_anomaly_detector(state)
    state = node_merchant_analyzer(state)
    state = node_report_builder(state)

    return {
        "categorized_df": state["categorized_df"],
        "workflow_steps": state["workflow_steps"],
        "workflow_engine": state["workflow_engine"],
        "total_expenses": state["total_expenses"],
        "total_credits": state["total_credits"],
        "surplus": state["savings_result"]["surplus"],
        "savings_rate": state["savings_result"]["savings_rate"],
        "recommended_savings_target": state["savings_result"]["recommended_savings_target"],
        "savings_strategy_level": state["savings_result"]["strategy_level"],
        "biggest_category": state["biggest_category"],
        "debt_spend": state["debt_result"]["debt_spend"],
        "debt_ratio": state["debt_result"]["debt_ratio"],
        "debt_status": state["debt_result"]["debt_status"],
        "document_reader": state["document_reader_output"],
        "expense_classifier": state["expense_classifier_output"],
        "debt_analyzer": state["debt_analyzer_output"],
        "savings_strategist": state["savings_strategist_output"],
        "report_builder": state["report_builder_output"],
        "orchestration_note": state["orchestration_note"],
        "recurring_df": state["recurring_df"],
        "recurring_count": state["recurring_count"],
        "recurring_summary": state["recurring_summary"],
        "unusual_df": state["unusual_df"],
        "unusual_count": state["unusual_count"],
        "unusual_summary": state["unusual_summary"],
        "merchant_df": state["merchant_df"],
        "top_merchant_summary": state["top_merchant_summary"],
        "budget_health_score": state["budget_health_score"],
        "budget_health_label": state["budget_health_label"],
    }