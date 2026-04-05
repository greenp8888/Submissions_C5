"""
FinanceDoctor — Dashboard Visualizations (Layer 4)
====================================================
Plotly-based charts for financial data analysis.
All charts use a consistent dark theme matching the app aesthetic.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ─────────────────────────────────────────────
# COLOR PALETTE
# ─────────────────────────────────────────────

COLORS = {
    "gold": "#ffd200",
    "coral": "#ff6b6b",
    "green": "#38ef7d",
    "blue": "#3b82f6",
    "purple": "#a855f7",
    "teal": "#14b8a6",
    "orange": "#f97316",
    "pink": "#ec4899",
    "slate": "#64748b",
    "bg_dark": "#0f0f1a",
    "bg_card": "#1a1a2e",
    "text_muted": "#9ca3af",
}

CATEGORY_COLORS = [
    "#ff6b6b", "#ffd200", "#38ef7d", "#3b82f6", "#a855f7",
    "#14b8a6", "#f97316", "#ec4899", "#64748b", "#06b6d4",
    "#84cc16", "#e11d48", "#8b5cf6", "#0ea5e9",
]

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#e0e0ff"),
    margin=dict(l=20, r=20, t=40, b=20),
)


# ─────────────────────────────────────────────
# COLUMN DETECTION
# ─────────────────────────────────────────────

def detect_columns(df: pd.DataFrame) -> dict:
    """Auto-detect column roles from column names."""
    mapping = {
        "date": None, "amount": None, "category": None,
        "type": None, "description": None, "balance": None,
    }

    for col in df.columns:
        cl = col.lower().strip()
        if mapping["date"] is None and any(k in cl for k in ["date", "time", "period"]):
            mapping["date"] = col
        elif mapping["amount"] is None and any(k in cl for k in ["amount", "value", "sum"]):
            mapping["amount"] = col
        elif mapping["category"] is None and any(k in cl for k in ["category", "categ", "head"]):
            mapping["category"] = col
        elif mapping["type"] is None and cl in ("type", "cr/dr", "direction", "txn type"):
            mapping["type"] = col
        elif mapping["description"] is None and any(k in cl for k in ["desc", "narr", "particular", "remark"]):
            mapping["description"] = col
        elif mapping["balance"] is None and any(k in cl for k in ["balance", "bal", "closing"]):
            mapping["balance"] = col

    # Support split Credit and Debit columns if Amount / Type are missing
    if mapping["amount"] is None or mapping["type"] is None:
        credit_col = next((c for c in df.columns if c.lower().strip() in ["credit", "deposit", "cr", "deposits", "deposit amount", "credit amount", "credits"]), None)
        debit_col = next((c for c in df.columns if c.lower().strip() in ["debit", "withdrawal", "dr", "withdrawals", "withdrawal amount", "debit amount", "debits"]), None)
        
        if credit_col and debit_col:
            cr_vals = pd.to_numeric(df[credit_col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
            dr_vals = pd.to_numeric(df[debit_col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
            
            df["_Parsed_Amount"] = cr_vals + dr_vals
            df["_Parsed_Type"] = cr_vals.apply(lambda x: "Credit" if x > 0 else "Debit")
            
            mapping["amount"] = "_Parsed_Amount"
            mapping["type"] = "_Parsed_Type"
            
    # As a secondary fallback, dynamically clean the amount column if it was detected but is stringified
    if mapping["amount"] and not pd.api.types.is_numeric_dtype(df[mapping["amount"]]):
        try:
            df[mapping["amount"]] = pd.to_numeric(df[mapping["amount"]].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        except:
            pass

    return mapping


# ─────────────────────────────────────────────
# FINANCIAL SUMMARY CARDS
# ─────────────────────────────────────────────

def render_summary_cards(df: pd.DataFrame, col_map: dict):
    """Render key financial metric cards."""
    amt_col = col_map.get("amount")
    type_col = col_map.get("type")

    if amt_col is None or type_col is None:
        st.info("📊 Upload data with 'Amount' and 'Type' columns to see summary metrics.")
        return

    credits = df[df[type_col].str.lower() == "credit"][amt_col].sum()
    debits = df[df[type_col].str.lower() == "debit"][amt_col].sum()
    net = credits - debits
    savings_rate = (net / credits * 100) if credits > 0 else 0

    def _format_inr(val):
        """Format as ₹ with Indian comma notation."""
        if abs(val) >= 1e7:
            return f"₹{val / 1e7:.2f} Cr"
        elif abs(val) >= 1e5:
            return f"₹{val / 1e5:.2f} L"
        else:
            return f"₹{val:,.0f}"

    cols = st.columns(4)
    metrics = [
        ("Total Income", credits, COLORS["green"], "📈"),
        ("Total Expenses", debits, COLORS["coral"], "📉"),
        ("Net Savings", net, COLORS["gold"] if net >= 0 else COLORS["coral"], "💰"),
        ("Savings Rate", f"{savings_rate:.1f}%", COLORS["blue"], "📊"),
    ]

    for col, (label, value, color, icon) in zip(cols, metrics):
        display_val = value if isinstance(value, str) else _format_inr(value)
        col.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border: 1px solid #2d2d44;
            border-radius: 12px;
            padding: 18px;
            text-align: center;
            border-left: 4px solid {color};
        ">
            <div style="font-size: 1.5rem; margin-bottom: 4px;">{icon}</div>
            <div style="font-size: 1.3rem; font-weight: 700; color: {color};">{display_val}</div>
            <div style="font-size: 0.75rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px;">{label}</div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SPENDING BREAKDOWN PIE CHART
# ─────────────────────────────────────────────

def render_spending_breakdown(df: pd.DataFrame, col_map: dict):
    """Category-wise expense donut chart."""
    amt_col = col_map.get("amount")
    type_col = col_map.get("type")
    cat_col = col_map.get("category")

    if not all([amt_col, type_col, cat_col]):
        st.info("Need 'Amount', 'Type', and 'Category' columns for spending breakdown.")
        return

    expenses = df[df[type_col].str.lower() == "debit"].copy()
    # Exclude EMI/Investment for pure spending view
    spending = expenses[~expenses[cat_col].isin(["Investment", "Loan/EMI", "Insurance"])]

    if spending.empty:
        st.info("No spending data found.")
        return

    by_cat = spending.groupby(cat_col)[amt_col].sum().sort_values(ascending=False).reset_index()

    fig = px.pie(
        by_cat,
        values=amt_col,
        names=cat_col,
        hole=0.45,
        color_discrete_sequence=CATEGORY_COLORS,
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="💸 Spending by Category", font=dict(size=16)),
        showlegend=True,
        legend=dict(font=dict(size=11)),
        height=380,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont_size=11,
    )
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# MONTHLY INCOME vs EXPENSES BAR CHART
# ─────────────────────────────────────────────

def render_monthly_trends(df: pd.DataFrame, col_map: dict):
    """Monthly income vs expenses grouped bar chart."""
    amt_col = col_map.get("amount")
    type_col = col_map.get("type")
    date_col = col_map.get("date")

    if not all([amt_col, type_col, date_col]):
        st.info("Need 'Amount', 'Type', and 'Date' columns for monthly trends.")
        return

    df_copy = df.copy()
    df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors="coerce")
    df_copy = df_copy.dropna(subset=[date_col])
    df_copy["Month"] = df_copy[date_col].dt.to_period("M").astype(str)

    income = df_copy[df_copy[type_col].str.lower() == "credit"].groupby("Month")[amt_col].sum()
    expenses = df_copy[df_copy[type_col].str.lower() == "debit"].groupby("Month")[amt_col].sum()

    months = sorted(set(income.index) | set(expenses.index))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=months,
        y=[income.get(m, 0) for m in months],
        name="Income",
        marker_color=COLORS["green"],
        marker_line_width=0,
    ))
    fig.add_trace(go.Bar(
        x=months,
        y=[expenses.get(m, 0) for m in months],
        name="Expenses",
        marker_color=COLORS["coral"],
        marker_line_width=0,
    ))

    # Net savings line
    net = [income.get(m, 0) - expenses.get(m, 0) for m in months]
    fig.add_trace(go.Scatter(
        x=months,
        y=net,
        name="Net Savings",
        mode="lines+markers",
        line=dict(color=COLORS["gold"], width=3),
        marker=dict(size=8),
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="📅 Monthly Income vs Expenses", font=dict(size=16)),
        barmode="group",
        height=400,
        xaxis=dict(title="Month", gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(title="Amount (₹)", gridcolor="rgba(255,255,255,0.05)"),
        legend=dict(orientation="h", y=-0.15),
    )
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# DEBT / EMI ANALYSIS
# ─────────────────────────────────────────────

def render_debt_analysis(df: pd.DataFrame, col_map: dict):
    """Debt/EMI breakdown visualization."""
    amt_col = col_map.get("amount")
    type_col = col_map.get("type")
    cat_col = col_map.get("category")
    desc_col = col_map.get("description")
    date_col = col_map.get("date")

    if not all([amt_col, type_col]):
        st.info("Need 'Amount' and 'Type' columns for debt analysis.")
        return

    expenses = df[df[type_col].str.lower() == "debit"].copy()

    # Find debt-related transactions
    debt_keywords = ["emi", "loan", "credit card", "personal loan", "home loan", "car loan"]
    if cat_col:
        debt_txns = expenses[expenses[cat_col].str.lower().isin(["loan/emi", "emi", "loan"])]
        if debt_txns.empty and desc_col:
            mask = expenses[desc_col].str.lower().apply(
                lambda x: any(k in str(x) for k in debt_keywords)
            )
            debt_txns = expenses[mask]
    elif desc_col:
        mask = expenses[desc_col].str.lower().apply(
            lambda x: any(k in str(x) for k in debt_keywords)
        )
        debt_txns = expenses[mask]
    else:
        st.info("Need 'Category' or 'Description' column for debt analysis.")
        return

    if debt_txns.empty:
        st.success("🎉 No debt/EMI transactions detected! You're debt-free based on this data.")
        return

    # Group by description for breakdown
    group_col = desc_col if desc_col else cat_col
    if group_col:
        by_loan = debt_txns.groupby(group_col)[amt_col].sum().sort_values(ascending=True).reset_index()

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=by_loan[group_col],
            x=by_loan[amt_col],
            orientation="h",
            marker=dict(
                color=by_loan[amt_col],
                colorscale=[[0, COLORS["orange"]], [1, COLORS["coral"]]],
            ),
            text=[f"₹{v:,.0f}" for v in by_loan[amt_col]],
            textposition="auto",
        ))

        fig.update_layout(
            **PLOTLY_LAYOUT,
            title=dict(text="🏦 Debt / EMI Breakdown (Total Paid)", font=dict(size=16)),
            height=350,
            xaxis=dict(title="Total Amount (₹)", gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(title=""),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    # Monthly debt payments
    if date_col:
        debt_txns_copy = debt_txns.copy()
        debt_txns_copy[date_col] = pd.to_datetime(debt_txns_copy[date_col], errors="coerce")
        debt_txns_copy = debt_txns_copy.dropna(subset=[date_col])
        debt_txns_copy["Month"] = debt_txns_copy[date_col].dt.to_period("M").astype(str)
        monthly_debt = debt_txns_copy.groupby("Month")[amt_col].sum().reset_index()

        total_monthly_avg = monthly_debt[amt_col].mean()
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); border: 1px solid #ff416c; border-radius: 10px; padding: 14px; margin: 8px 0;">
            <span style="color: #ff6b6b; font-weight: 600;">⚠️ Average Monthly Debt Obligation:</span>
            <span style="color: #ffd200; font-weight: 700; font-size: 1.1rem;"> ₹{total_monthly_avg:,.0f}</span>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SAVINGS & INVESTMENT TRACKER
# ─────────────────────────────────────────────

def render_savings_tracker(df: pd.DataFrame, col_map: dict):
    """Investment & savings tracking visualization."""
    amt_col = col_map.get("amount")
    type_col = col_map.get("type")
    cat_col = col_map.get("category")
    desc_col = col_map.get("description")
    date_col = col_map.get("date")

    if not all([amt_col, type_col]):
        st.info("Need 'Amount' and 'Type' columns for savings tracking.")
        return

    expenses = df[df[type_col].str.lower() == "debit"].copy()

    # Find investment transactions
    invest_keywords = ["sip", "ppf", "mutual fund", "elss", "nps", "fd", "investment", "mf"]
    if cat_col:
        invest_txns = expenses[expenses[cat_col].str.lower().isin(["investment", "savings"])]
        if invest_txns.empty and desc_col:
            mask = expenses[desc_col].str.lower().apply(
                lambda x: any(k in str(x) for k in invest_keywords)
            )
            invest_txns = expenses[mask]
    elif desc_col:
        mask = expenses[desc_col].str.lower().apply(
            lambda x: any(k in str(x) for k in invest_keywords)
        )
        invest_txns = expenses[mask]
    else:
        st.info("Need 'Category' or 'Description' for savings tracking.")
        return

    if invest_txns.empty:
        st.warning("⚠️ No investment/savings transactions found. Consider starting SIPs!")
        return

    total_invested = invest_txns[amt_col].sum()

    # Investment breakdown
    group_col = desc_col if desc_col else cat_col
    if group_col:
        by_type = invest_txns.groupby(group_col)[amt_col].sum().sort_values(ascending=False).reset_index()

        fig = px.pie(
            by_type,
            values=amt_col,
            names=group_col,
            hole=0.5,
            color_discrete_sequence=[COLORS["green"], COLORS["teal"], COLORS["blue"], COLORS["purple"]],
        )
        fig.update_layout(
            **PLOTLY_LAYOUT,
            title=dict(text="💰 Investment Allocation", font=dict(size=16)),
            height=350,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label", textfont_size=11)
        st.plotly_chart(fig, use_container_width=True)

    # Monthly investment trend
    if date_col:
        inv_copy = invest_txns.copy()
        inv_copy[date_col] = pd.to_datetime(inv_copy[date_col], errors="coerce")
        inv_copy = inv_copy.dropna(subset=[date_col])
        inv_copy["Month"] = inv_copy[date_col].dt.to_period("M").astype(str)
        monthly_inv = inv_copy.groupby("Month")[amt_col].sum().reset_index()

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=monthly_inv["Month"],
            y=monthly_inv[amt_col],
            marker_color=COLORS["green"],
            text=[f"₹{v:,.0f}" for v in monthly_inv[amt_col]],
            textposition="auto",
        ))
        fig2.update_layout(
            **PLOTLY_LAYOUT,
            title=dict(text="📈 Monthly Investment Amount", font=dict(size=16)),
            height=300,
            xaxis=dict(title="Month"),
            yaxis=dict(title="Invested (₹)", gridcolor="rgba(255,255,255,0.05)"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a1a2e, #16213e); border: 1px solid #38ef7d; border-radius: 10px; padding: 14px; margin: 8px 0;">
        <span style="color: #38ef7d; font-weight: 600;">✅ Total Invested (this period):</span>
        <span style="color: #ffd200; font-weight: 700; font-size: 1.1rem;"> ₹{total_invested:,.0f}</span>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TOP EXPENSES TABLE
# ─────────────────────────────────────────────

def render_top_expenses(df: pd.DataFrame, col_map: dict, top_n: int = 10):
    """Show top N largest expenses."""
    amt_col = col_map.get("amount")
    type_col = col_map.get("type")
    desc_col = col_map.get("description")
    date_col = col_map.get("date")
    cat_col = col_map.get("category")

    if not all([amt_col, type_col]):
        return

    expenses = df[df[type_col].str.lower() == "debit"].copy()
    top = expenses.nlargest(top_n, amt_col)

    display_cols = [c for c in [date_col, desc_col, cat_col, amt_col] if c is not None]
    if display_cols:
        display_df = top[display_cols].copy()
        if amt_col in display_df.columns:
            display_df[amt_col] = display_df[amt_col].apply(lambda x: f"₹{x:,.0f}")
        st.markdown(f"### 🔝 Top {top_n} Largest Expenses")
        st.dataframe(display_df, use_container_width=True, hide_index=True)
