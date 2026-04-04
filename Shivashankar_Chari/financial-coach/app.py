import os
from typing import Dict, Any, List

from agents.debt_analyzer import analyze_debt, format_debt_output

import pandas as pd
import plotly.express as px
import streamlit as st

from agents.document_reader import (
    load_transactions,
    validate_uploaded_file,
    get_supported_file_message,
    get_current_backend_support_message,
)
from agents.expense_classifier import (
    add_categories,
    get_category_summary,
    get_biggest_category,
)


# Page setup
st.set_page_config(
    page_title="AI Financial Coach",
    page_icon="💰",
    layout="wide",
)


# Model options
OPENROUTER_FREE_MODELS = [
    "google/gemini-2.0-flash-exp",
    "google/gemini-2.5-flash",
    "meta-llama/llama-3.1-8b-instruct",
    "mistralai/mistral-7b-instruct",
    "qwen/qwen2.5-7b-instruct",
]

HUGGINGFACE_FREE_MODELS = [
    "Qwen/Qwen2.5-7B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "HuggingFaceH4/zephyr-7b-beta",
]


# Session state
def initialize_session_state() -> None:
    """Initialize session state variables."""
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
                "content": "Upload your bank statement and I will help analyze spending, debt pressure, and savings opportunities.",
            }
        ],
        "deep_research_focus": "Savings improvement",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_uploaded_data() -> None:
    """Clear uploaded file state."""
    st.session_state.transactions_df = None
    st.session_state.uploaded_file_name = None
    st.session_state.processing_error = None
    st.session_state.analysis_started = False
    st.session_state.agent_outputs = {}
    st.session_state.categorized_df = None


def run_basic_analysis(
    df: pd.DataFrame,
    monthly_income: float,
    primary_goal: str,
    ai_vendor: str,
    model_name: str,
    rag_enabled: bool,
    mcp_mode: bool,
    langsmith_enabled: bool,
) -> Dict[str, Any]:
    """Create initial multi-agent outputs using loaded transaction data."""
    working_df = add_categories(df)

    expense_df = working_df[working_df["amount"] < 0].copy()
    income_df = working_df[working_df["amount"] > 0].copy()

    total_expenses = abs(expense_df["amount"].sum()) if not expense_df.empty else 0
    total_credits = income_df["amount"].sum() if not income_df.empty else 0
    surplus = monthly_income - total_expenses
    savings_rate = (surplus / monthly_income * 100) if monthly_income > 0 else 0

    biggest_category = get_biggest_category(working_df)
    category_summary = get_category_summary(working_df)

    if category_summary:
        category_summary_text = " | ".join(
            [f"{cat}: ₹{amt:,.0f}" for cat, amt in category_summary.items()]
        )
    else:
        category_summary_text = "No category data available."

    date_range_text = "N/A"
    if not working_df.empty and "date" in working_df.columns:
        min_date = working_df["date"].min()
        max_date = working_df["date"].max()
        if pd.notna(min_date) and pd.notna(max_date):
            date_range_text = f"{min_date.strftime('%d %b %Y')} to {max_date.strftime('%d %b %Y')}"

    orchestration_note = (
        f"LangGraph-ready orchestration | RAG={'ON' if rag_enabled else 'OFF'} | "
        f"MCP-inspired tools={'ON' if mcp_mode else 'OFF'} | "
        f"LangSmith tracing={'ON' if langsmith_enabled else 'OFF'}"
    )

    document_reader_output = (
        f"Processed {len(working_df)} transactions successfully. "
        f"Date range: {date_range_text}. Input normalized for downstream agents."
    )

    expense_classifier_output = (
        f"Category summary → {category_summary_text}. "
        f"Biggest category: {biggest_category}."
    )

    debt_result = analyze_debt(working_df, monthly_income)
    debt_analyzer_output = format_debt_output(debt_result)

    savings_strategist_output = (
        f"With monthly income ₹{monthly_income:,.0f} and estimated surplus ₹{surplus:,.0f}, "
        f"focus on goal: {primary_goal}. "
        "Recommended next step: cap discretionary spends, define monthly save target, "
        "and allocate fixed amount toward debt or emergency corpus first."
    )

    report_builder_output = (
        f"Financial snapshot → expenses: ₹{total_expenses:,.0f}, income credits in file: ₹{total_credits:,.0f}, "
        f"estimated surplus: ₹{surplus:,.0f}, savings rate: {savings_rate:.1f}%. "
        f"AI setup: {ai_vendor} using model {model_name}. {orchestration_note}."
    )

    return {
        "categorized_df": working_df,
        "total_expenses": round(total_expenses, 2),
        "total_credits": round(total_credits, 2),
        "surplus": round(surplus, 2),
        "savings_rate": round(savings_rate, 1),
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
    }


def render_metric_card(label: str, value: str) -> None:
    """Render a metric using Streamlit metric widget."""
    st.metric(label, value)


def build_quick_summary(outputs: Dict[str, Any]) -> List[str]:
    """Build quick insight bullets for deep research and chat summary."""
    if not outputs:
        return []

    bullets = [
        f"Top spending category: {outputs.get('biggest_category', 'N/A')}",
        f"Savings rate: {outputs.get('savings_rate', 0):.1f}%",
        f"Debt status: {outputs.get('debt_status', 'N/A')}",
    ]

    surplus = outputs.get("surplus", 0)
    if surplus < 0:
        bullets.append("Monthly expenses are above stated income, so budget correction is needed.")
    elif surplus < 10000:
        bullets.append("Surplus exists but is limited, so controlling variable spend will help.")
    else:
        bullets.append("You have usable surplus that can be split across savings and debt reduction.")

    return bullets


def render_visual_analytics(df: pd.DataFrame) -> None:
    """Render charts and visual analytics."""
    if df is None or df.empty:
        st.info("No data available for charts yet.")
        return

    expense_df = df[df["amount"] < 0].copy()
    income_df = df[df["amount"] > 0].copy()

    chart_tab1, chart_tab2, chart_tab3, chart_tab4 = st.tabs(
        ["Category Mix", "Top Categories", "Spending Trend", "Credit vs Debit"]
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
            st.info("No expense category data available for pie chart.")

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
                category_spend,
                x="category",
                y="amount",
                title="Top Spending Categories",
                text="amount",
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No expense category data available for bar chart.")

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
            st.info("Date column unavailable for spending trend.")

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


def render_sidebar() -> None:
    """Render product-style sidebar."""
    outputs = st.session_state.agent_outputs

    st.markdown("## Financial Account")
    if st.session_state.uploaded_file_name:
        st.success(f"Connected to {st.session_state.uploaded_file_name}")
    else:
        st.info("Upload a file to connect your account")

    st.divider()

    st.markdown("## Navigation")
    st.session_state.nav_option = st.radio(
        "",
        ["My Portfolio", "Deep Research", "Chat with AI"],
        index=["My Portfolio", "Deep Research", "Chat with AI"].index(st.session_state.nav_option),
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("## Summary")
    if outputs:
        st.metric("Total Credits", f"₹{outputs.get('total_credits', 0):,.0f}")
        st.metric("Total Expenses", f"₹{outputs.get('total_expenses', 0):,.0f}")
        st.metric("Net Surplus", f"₹{outputs.get('surplus', 0):,.0f}")
        st.caption(f"Savings Rate: {outputs.get('savings_rate', 0):.1f}%")
        st.caption(f"Debt Status: {outputs.get('debt_status', 'N/A')}")
    else:
        st.caption("Run analysis to view summary metrics.")

    st.divider()

    if st.button("Clear Analysis", use_container_width=True):
        reset_uploaded_data()
        st.rerun()

    with st.expander("Available Tools", expanded=False):
        st.markdown(
            """
            - Document Reader
            - Expense Classifier
            - Debt Analyzer
            - Savings Strategist
            - Report Builder
            """
        )

    with st.expander("Settings", expanded=False):
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
                else 1,
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
            "Enable RAG mode",
            value=st.session_state.rag_enabled,
        )
        st.session_state.mcp_mode = st.checkbox(
            "Enable MCP-inspired tool mode",
            value=st.session_state.mcp_mode,
        )

    st.divider()
    st.caption(get_supported_file_message())
    st.caption(get_current_backend_support_message())


def render_upload_panel() -> None:
    """Render upload and analysis controls."""
    st.subheader("Portfolio Input")

    uploaded_file = st.file_uploader(
        "Bank statement, salary slip, or expense file",
        type=["csv", "xlsx", "xls", "pdf", "png", "jpg", "jpeg"],
        help="Supported formats: CSV, Excel, PDF, PNG, JPG, JPEG | Max file size: 5 MB",
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
            outputs = run_basic_analysis(
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
            st.session_state.categorized_df = outputs["categorized_df"]
            st.success("Analysis completed successfully.")


def render_portfolio_view() -> None:
    """Render portfolio overview page."""
    st.title("AI Financial Coach")
    st.caption("Analyze your bank statement, understand spending behavior, and surface financial improvement opportunities.")

    left_col, right_col = st.columns([0.9, 1.6], gap="large")

    with left_col:
        render_upload_panel()

    with right_col:
        outputs = st.session_state.agent_outputs

        st.subheader("Portfolio Overview")

        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

        with metric_col1:
            render_metric_card("Credits", f"₹{outputs.get('total_credits', 0):,.0f}")

        with metric_col2:
            render_metric_card("Expenses", f"₹{outputs.get('total_expenses', 0):,.0f}")

        with metric_col3:
            render_metric_card("Surplus", f"₹{outputs.get('surplus', 0):,.0f}")

        with metric_col4:
            render_metric_card("Savings Rate", f"{outputs.get('savings_rate', 0):.1f}%")

        st.divider()

        if st.session_state.analysis_started and outputs:
            insight_tab1, insight_tab2, insight_tab3 = st.tabs(
                ["AI Insights", "Transactions Detail", "Schema"]
            )

            with insight_tab1:
                with st.container(border=True):
                    st.subheader("Financial Insight Summary")
                    quick_summary = build_quick_summary(outputs)
                    for item in quick_summary:
                        st.markdown(f"- {item}")

                agent_col1, agent_col2 = st.columns(2)

                with agent_col1:
                    with st.container(border=True):
                        st.caption("Document Reader")
                        st.write(outputs.get("document_reader", "No output yet."))

                    with st.container(border=True):
                        st.caption("Expense Classifier")
                        st.write(outputs.get("expense_classifier", "No output yet."))

                    with st.container(border=True):
                        st.caption("Debt Analyzer")
                        st.write(outputs.get("debt_analyzer", "No output yet."))

                with agent_col2:
                    with st.container(border=True):
                        st.caption("Savings Strategist")
                        st.write(outputs.get("savings_strategist", "No output yet."))

                    with st.container(border=True):
                        st.caption("Report Builder")
                        st.write(outputs.get("report_builder", "No output yet."))

            with insight_tab2:
                if st.session_state.categorized_df is not None:
                    st.subheader("Transactions Detail")
                    render_visual_analytics(st.session_state.categorized_df)
                    st.dataframe(st.session_state.categorized_df, use_container_width=True, height=420)
                else:
                    st.info("No transaction data available yet.")

            with insight_tab3:
                if st.session_state.categorized_df is not None:
                    schema_df = pd.DataFrame(
                        {
                            "column": st.session_state.categorized_df.columns,
                            "dtype": [str(dtype) for dtype in st.session_state.categorized_df.dtypes],
                        }
                    )
                    st.dataframe(schema_df, use_container_width=True, height=420)
                else:
                    st.info("No schema to display yet.")
        else:
            st.info("Upload a file and run analysis to unlock portfolio insights.")


def render_deep_research_view() -> None:
    """Render research view."""
    st.title("Deep Research")
    st.caption("Run targeted analysis on one financial focus area at a time.")

    outputs = st.session_state.agent_outputs

    if not outputs:
        st.info("Run portfolio analysis first to activate deep research.")
        return

    focus_area = st.selectbox(
        "Select a focus area",
        [
            "Savings improvement",
            "Debt pressure",
            "Overspending",
            "Budget discipline",
        ],
        index=[
            "Savings improvement",
            "Debt pressure",
            "Overspending",
            "Budget discipline",
        ].index(st.session_state.deep_research_focus),
    )
    st.session_state.deep_research_focus = focus_area

    if st.button("Run Deep Research", type="primary", use_container_width=True):
        st.success(f"Deep research completed for: {focus_area}")

    with st.container(border=True):
        st.subheader("Research Summary")

        if focus_area == "Savings improvement":
            st.write(outputs.get("savings_strategist", "No savings insight available."))

        elif focus_area == "Debt pressure":
            st.write(outputs.get("debt_analyzer", "No debt insight available."))

        elif focus_area == "Overspending":
            st.write(outputs.get("expense_classifier", "No spending insight available."))

        else:
            st.write(outputs.get("report_builder", "No report insight available."))

    with st.container(border=True):
        st.subheader("Key Signals")
        for item in build_quick_summary(outputs):
            st.markdown(f"- {item}")


def render_chat_view() -> None:
    """Render simple AI chat view."""
    st.title("Chat with AI")
    st.caption("Ask questions about your spending, debt pressure, and savings potential.")

    outputs = st.session_state.agent_outputs

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    prompt = st.chat_input("Ask about your finances, spending, or savings...")

    if prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})

        response_parts = []

        if outputs:
            response_parts.append(f"Current surplus is ₹{outputs.get('surplus', 0):,.0f}.")
            response_parts.append(f"Top spending category is {outputs.get('biggest_category', 'N/A')}.")
            response_parts.append(f"Debt status is {outputs.get('debt_status', 'N/A')}.")
            response_parts.append(outputs.get("savings_strategist", ""))
        else:
            response_parts.append(
                "Upload and analyze a statement first so I can answer with specific financial context."
            )

        assistant_response = " ".join([part for part in response_parts if part])

        st.session_state.chat_messages.append(
            {"role": "assistant", "content": assistant_response}
        )

        st.rerun()


# Initialize app
initialize_session_state()

with st.sidebar:
    render_sidebar()

if st.session_state.nav_option == "My Portfolio":
    render_portfolio_view()
elif st.session_state.nav_option == "Deep Research":
    render_deep_research_view()
else:
    render_chat_view()