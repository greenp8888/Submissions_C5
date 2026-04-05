import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from agents.orchestrator import run_financial_coach, stream_financial_coach
from agents.state import FinancialState
import tempfile
import os

# ────────────────────────────────────────────────────────────
# Page config
# ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Financial Coach",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ────────────────────────────────────────────────────────────
# Session state defaults
# ────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────
# Theme / Personalisation
# ────────────────────────────────────────────────────────────
PRESETS: dict[str, dict[str, str]] = {
    "Light": {
        "bg":         "#f8f9fb",
        "sidebar_bg": "#ffffff",
        "card_bg":    "#ffffff",
        "text":       "#1a1a2e",
        "text_muted": "#6b7280",
        "accent":     "#4361ee",
        "accent_hover": "#3451d1",
        "border":     "#e5e7eb",
    },
    "Dark": {
        "bg":         "#0f1117",
        "sidebar_bg": "#1a1d27",
        "card_bg":    "#1e2130",
        "text":       "#e8eaf6",
        "text_muted": "#9ca3af",
        "accent":     "#818cf8",
        "accent_hover": "#6366f1",
        "border":     "#2d3748",
    },
    "Ocean": {
        "bg":         "#0a1628",
        "sidebar_bg": "#0d1e35",
        "card_bg":    "#112340",
        "text":       "#e0f2fe",
        "text_muted": "#7dd3fc",
        "accent":     "#38bdf8",
        "accent_hover": "#0ea5e9",
        "border":     "#1e4976",
    },
    "Warm": {
        "bg":         "#fdfaf7",
        "sidebar_bg": "#fff8f2",
        "card_bg":    "#ffffff",
        "text":       "#1c1917",
        "text_muted": "#78716c",
        "accent":     "#f97316",
        "accent_hover": "#ea6c0a",
        "border":     "#e7e5e4",
    },
}

with st.sidebar.expander("🎨 Personalise Theme", expanded=False):
    preset_name = st.radio(
        "Preset theme",
        options=list(PRESETS.keys()) + ["Custom"],
        index=0,
        label_visibility="collapsed",
    )
    if preset_name == "Custom":
        _d = PRESETS["Light"]
        c: dict[str, str] = {
            "bg":           st.color_picker("Background",       _d["bg"],         key="cp_bg"),
            "sidebar_bg":   st.color_picker("Sidebar",          _d["sidebar_bg"], key="cp_sb"),
            "card_bg":      st.color_picker("Card background",  _d["card_bg"],    key="cp_card"),
            "text":         st.color_picker("Primary text",     _d["text"],       key="cp_text"),
            "text_muted":   st.color_picker("Muted text",       _d["text_muted"], key="cp_muted"),
            "accent":       st.color_picker("Accent / buttons", _d["accent"],     key="cp_accent"),
            "accent_hover": _d["accent_hover"],
            "border":       st.color_picker("Borders",          _d["border"],     key="cp_border"),
        }
    else:
        c = PRESETS[preset_name]

# Inject comprehensive theme CSS
st.markdown(f"""
<style>
  /* ── Hide Streamlit built-in theme switcher ── */
  div[data-testid="colorThemeSelectLabel"],
  div[data-testid="colorThemeSelect"],
  div[class*="themeSelectContainer"],
  section[data-testid="stSidebarUserContent"] ~ div [data-testid="colorThemeSelect"] {{
      display: none !important;
  }}

  /* ── Google Font ── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  /* ── Base ── */
  html, body, [class*="css"], .stApp {{
      font-family: 'Inter', sans-serif !important;
  }}
  .stApp {{
      background-color: {c['bg']} !important;
      color: {c['text']} !important;
  }}

  /* ── Sidebar ── */
  section[data-testid="stSidebar"] {{
      background-color: {c['sidebar_bg']} !important;
      border-right: 1px solid {c['border']} !important;
  }}
  section[data-testid="stSidebar"] *,
  section[data-testid="stSidebar"] p,
  section[data-testid="stSidebar"] label,
  section[data-testid="stSidebar"] span,
  section[data-testid="stSidebar"] div {{
      color: {c['text']} !important;
  }}
  section[data-testid="stSidebar"] .stRadio label span {{
      color: {c['text']} !important;
  }}

  /* ── All text ── */
  p, li, span, label, div, td, th, caption {{
      color: {c['text']};
  }}
  h1, h2, h3, h4, h5, h6,
  .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
      color: {c['text']} !important;
      font-weight: 700 !important;
      letter-spacing: -0.02em;
  }}
  .stMarkdown p, .stMarkdown li, .stMarkdown span {{
      color: {c['text']} !important;
  }}

  /* ── Metric widgets ── */
  [data-testid="metric-container"] {{
      background-color: {c['card_bg']} !important;
      border: 1px solid {c['border']} !important;
      border-radius: 12px !important;
      padding: 16px !important;
      box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }}
  [data-testid="metric-container"] label,
  [data-testid="metric-container"] [data-testid="stMetricLabel"],
  [data-testid="metric-container"] [data-testid="stMetricLabel"] p {{
      color: {c['text_muted']} !important;
      font-size: 0.78rem !important;
      font-weight: 500 !important;
      text-transform: uppercase;
      letter-spacing: 0.05em;
  }}
  [data-testid="metric-container"] [data-testid="stMetricValue"],
  [data-testid="metric-container"] [data-testid="stMetricValue"] div {{
      color: {c['text']} !important;
      font-size: 1.6rem !important;
      font-weight: 700 !important;
  }}
  [data-testid="metric-container"] [data-testid="stMetricDelta"] {{
      font-size: 0.82rem !important;
  }}

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {{
      background-color: {c['card_bg']} !important;
      border-radius: 10px !important;
      border: 1px solid {c['border']} !important;
      padding: 4px !important;
      gap: 2px;
  }}
  .stTabs [data-baseweb="tab"] {{
      background-color: transparent !important;
      color: {c['text_muted']} !important;
      border-radius: 8px !important;
      font-weight: 500 !important;
      font-size: 0.9rem;
      padding: 8px 14px !important;
  }}
  .stTabs [aria-selected="true"] {{
      background-color: {c['accent']} !important;
      color: #ffffff !important;
  }}
  .stTabs [data-baseweb="tab-panel"] {{
      background-color: transparent !important;
      color: {c['text']} !important;
  }}

  /* ── Buttons ── */
  .stButton > button[kind="primary"] {{
      background: linear-gradient(135deg, {c['accent']}, {c['accent_hover']}) !important;
      color: #ffffff !important;
      border: none !important;
      border-radius: 10px !important;
      font-weight: 600 !important;
      font-size: 0.95rem !important;
      padding: 0.6rem 1.4rem !important;
      box-shadow: 0 4px 14px rgba(0,0,0,0.15);
      transition: all 0.2s ease !important;
  }}
  .stButton > button[kind="primary"]:hover {{
      transform: translateY(-1px) !important;
      box-shadow: 0 6px 20px rgba(0,0,0,0.2) !important;
  }}
  .stButton > button[kind="secondary"] {{
      background-color: {c['card_bg']} !important;
      color: {c['text']} !important;
      border: 1px solid {c['border']} !important;
      border-radius: 10px !important;
      font-weight: 500 !important;
  }}

  /* ── Inputs ── */
  .stTextInput input, .stTextArea textarea, .stSelectbox select,
  [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {{
      background-color: {c['card_bg']} !important;
      color: {c['text']} !important;
      border: 1px solid {c['border']} !important;
      border-radius: 8px !important;
  }}
  .stTextArea textarea {{
      background-color: {c['card_bg']} !important;
      color: {c['text']} !important;
  }}

  /* ── File uploader ── */
  [data-testid="stFileUploader"] {{
      background-color: {c['card_bg']} !important;
      border: 2px dashed {c['border']} !important;
      border-radius: 10px !important;
      color: {c['text']} !important;
  }}
  [data-testid="stFileUploader"] * {{ color: {c['text']} !important; }}

  /* ── Expander ── */
  [data-testid="stExpander"] {{
      background-color: {c['card_bg']} !important;
      border: 1px solid {c['border']} !important;
      border-radius: 10px !important;
  }}
  [data-testid="stExpander"] summary span,
  [data-testid="stExpander"] summary p {{
      color: {c['text']} !important;
      font-weight: 500;
  }}

  /* ── Tables / Dataframes ── */
  .stTable, table {{ color: {c['text']} !important; }}
  thead th {{
      background-color: {c['card_bg']} !important;
      color: {c['text_muted']} !important;
      border-bottom: 1px solid {c['border']} !important;
      font-weight: 600 !important;
      text-transform: uppercase;
      font-size: 0.75rem;
      letter-spacing: 0.06em;
  }}
  tbody td {{
      color: {c['text']} !important;
      border-bottom: 1px solid {c['border']} !important;
  }}
  [data-testid="stDataFrame"] {{
      border: 1px solid {c['border']} !important;
      border-radius: 10px !important;
      overflow: hidden;
  }}

  /* ── Progress bar ── */
  .stProgress > div > div > div > div {{
      background: linear-gradient(90deg, {c['accent']}, {c['accent_hover']}) !important;
      border-radius: 4px !important;
  }}
  .stProgress > div > div {{
      background-color: {c['border']} !important;
      border-radius: 4px !important;
  }}

  /* ── Info / Warning / Error / Success boxes ── */
  [data-testid="stAlert"] {{
      border-radius: 10px !important;
      border-left-width: 4px !important;
  }}
  [data-testid="stAlert"] p {{ color: inherit !important; }}

  /* ── Caption / small text ── */
  .stCaption, [data-testid="stCaptionContainer"] p {{
      color: {c['text_muted']} !important;
  }}

  /* ── Divider ── */
  hr {{ border-color: {c['border']} !important; opacity: 0.7; }}

  /* ── Selectbox / radio ── */
  [data-baseweb="select"] div,
  [data-baseweb="select"] span {{
      background-color: {c['card_bg']} !important;
      color: {c['text']} !important;
      border-color: {c['border']} !important;
  }}
  [data-baseweb="radio"] label span:last-child {{
      color: {c['text']} !important;
  }}

  /* ── Title / page header ── */
  .stApp header {{ background-color: transparent !important; }}
  [data-testid="stHeader"] {{ background-color: {c['bg']} !important; }}

  /* ── Tooltip ── */
  [data-baseweb="tooltip"] div {{
      background-color: {c['card_bg']} !important;
      color: {c['text']} !important;
      border: 1px solid {c['border']} !important;
  }}
</style>
""", unsafe_allow_html=True)


# ────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────

def _render_step_log(step_log: list[dict]):
    """Render an accumulated list of step progress messages."""
    status_icons = {"running": "🔄", "done": "✅", "error": "❌"}
    for s in step_log:
        icon = status_icons.get(s["status"], "•")
        if s["status"] == "running":
            st.info(f"{icon} {s['text']}")
        else:
            st.success(f"{icon} {s['text']}")


def _format_step_summary(event: dict) -> str:
    """Format a step_done event into a short summary string."""
    s = event.get("summary", {})
    agent = event.get("agent", "")

    summaries = {
        "document_ingestion": (
            f"Parsed {s.get('transaction_count', '?')} transactions — "
            f"Income ${s.get('total_income', 0):,.2f}, "
            f"Expenses ${s.get('total_expenses', 0):,.2f}, "
            f"Savings rate {s.get('savings_rate', 0)}%"
        ),
        "financial_analyzer": (
            f"Health score: **{s.get('health_score', '?')}/100** — "
            f"{s.get('insights_count', 0)} insights generated"
        ),
        "debt_strategist": (
            f"Debt detected: **{'Yes' if s.get('has_debt') else 'No'}** — "
            f"Strategy: {s.get('strategy', 'N/A')}"
        ),
        "savings_strategy": (
            f"Emergency fund target: ${s.get('emergency_target', 0):,.2f} — "
            f"{s.get('goals_count', 0)} savings goals set"
        ),
        "budget_advisor": (
            f"{s.get('categories_budgeted', 0)} categories budgeted — "
            f"Surplus: ${s.get('surplus', 0):,.2f}"
        ),
        "report_generator": (
            f"Report compiled ({s.get('report_length', 0)} characters)"
        ),
    }
    return summaries.get(agent, "")


def _metric_card(label: str, value: str, emoji: str):
    st.markdown(f"""
    <div style="
        background:{c['card_bg']};
        border:1px solid {c['border']};
        border-radius:14px;
        padding:20px 16px;
        text-align:center;
        box-shadow:0 2px 8px rgba(0,0,0,0.07);
        transition:transform 0.15s ease;
    ">
        <div style="font-size:2rem;margin-bottom:6px">{emoji}</div>
        <div style="font-size:0.72rem;color:{c['text_muted']};font-weight:600;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:4px">{label}</div>
        <div style="font-size:1.5rem;font-weight:700;color:{c['text']}">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def _score_emoji(score: float | None) -> str:
    if score is None:
        return "❓"
    if score >= 90: return "🟢"
    if score >= 70: return "🔵"
    if score >= 50: return "🟡"
    if score >= 30: return "🟠"
    return "🔴"


def _render_insights(insights: list):
    severity_order = {"critical": 0, "warning": 1, "info": 2, "positive": 3}
    icons = {"critical": "🔴", "warning": "🟠", "info": "🔵", "positive": "🟢"}
    sorted_insights = sorted(insights, key=lambda x: severity_order.get(x.get("severity", "info"), 2))
    for i in sorted_insights:
        icon = icons.get(i.get("severity", "info"), "⚪")
        st.markdown(f"**{icon} {i.get('category', '').title()}** — {i.get('finding', '')}")
        st.caption(f"💡 {i.get('recommendation', '')}")
        st.divider()


def _render_budget(budget: dict):
    allocations = budget.get("allocations", [])
    if not allocations:
        st.info("No budget recommendations available.")
        return
    st.subheader("Budget Allocations")
    sorted_allocs = sorted(allocations, key=lambda x: x.get("current_avg", 0), reverse=True)
    cols = ["Category", "Current ($/mo)", "Recommended ($/mo)", "Change (%)", "Note"]
    rows = []
    for a in sorted_allocs:
        var = a.get("variance_pct", 0)
        rows.append([
            a["category"],
            f'{a.get("current_avg", 0):,.2f}',
            f'{a.get("recommended", 0):,.2f}',
            f"{var:+.0f}%",
            a.get("note", ""),
        ])
    st.table({cols[i]: [r[i] for r in rows] for i in range(len(cols))})
    alerts = budget.get("alerts", [])
    if alerts:
        st.subheader("⚠️ Alerts")
        for a in alerts:
            st.warning(f"**[{a['type']}] {a['category']}**: {a['message']}")


def _render_savings(plan: dict):
    if not plan:
        st.info("No savings plan available.")
        return
    ef = plan.get("emergency_fund", {})
    if ef:
        st.subheader("🛡️ Emergency Fund")
        c1, c2, c3 = st.columns(3)
        c1.metric("Target", f"${ef.get('target_amount', 0):,.2f}")
        c2.metric("Monthly", f"${ef.get('monthly_contribution', 0):,.2f}")
        c3.metric("Months to Goal", ef.get("months_to_fund", 0))
    goals = plan.get("savings_goals", [])
    if goals:
        st.subheader("🎯 Savings Goals")
        for g in goals:
            st.markdown(f"**{g.get('label', '')}** ({g.get('goal', '')})")
            st.caption(f"${g.get('monthly_contribution', 0):,.2f}/mo → ${g.get('target_amount', 0):,.2f} in {g.get('timeline_months', 0)} months")
    quick_wins = plan.get("quick_wins", [])
    if quick_wins:
        st.subheader("⚡ Quick Wins")
        for w in quick_wins:
            st.markdown(f"• {w}")

    bank_offers = plan.get("bank_offers", [])
    if bank_offers:
        st.subheader("🌐 Top High-Interest Savings Offers")
        st.caption("Live results from the web — verify rates directly with each bank.")
        for offer in bank_offers:
            title = offer.get("title", "")
            url = offer.get("url", "")
            snippet = offer.get("snippet", "")
            if title and url:
                st.markdown(f"**[{title}]({url})**")
            elif title:
                st.markdown(f"**{title}**")
            if snippet:
                st.caption(snippet)
            st.divider()


def _plotly_theme() -> dict:
    """Return a consistent plotly layout dict matching the active colour theme."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=c["text"], family="Inter, sans-serif"),
        xaxis=dict(gridcolor=c["border"], linecolor=c["border"], tickfont=dict(color=c["text_muted"])),
        yaxis=dict(gridcolor=c["border"], linecolor=c["border"], tickfont=dict(color=c["text_muted"])),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=c["text"])),
        margin=dict(t=60, b=40, l=10, r=10),
    )


def _render_charts(charts: dict):
    if not charts:
        st.info("No charts available.")
        return
    if "expense_breakdown" in charts:
        ch_data = charts["expense_breakdown"]
        fig = go.Figure(data=[go.Pie(
            labels=ch_data["labels"], values=ch_data["values"], hole=0.45,
            marker=dict(line=dict(color=c["bg"], width=2)),
        )])
        fig.update_layout(title=dict(text=ch_data["title"], font=dict(color=c["text"])), **_plotly_theme())
        st.plotly_chart(fig, use_container_width=True)
    if "income_vs_expense" in charts:
        ch_data = charts["income_vs_expense"]
        fig = go.Figure(data=[go.Bar(
            x=ch_data["categories"], y=ch_data["values"],
            marker_color=[c["accent"], "#ef4444", "#10b981"],
            marker_line_width=0,
        )])
        fig.update_layout(title=dict(text=ch_data["title"], font=dict(color=c["text"])), **_plotly_theme())
        st.plotly_chart(fig, use_container_width=True)
    if "budget_comparison" in charts:
        ch_data = charts["budget_comparison"]
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Current",     x=ch_data["categories"], y=ch_data["current"],     marker_color=c["text_muted"], marker_line_width=0))
        fig.add_trace(go.Bar(name="Recommended", x=ch_data["categories"], y=ch_data["recommended"], marker_color=c["accent"],     marker_line_width=0))
        fig.update_layout(title=dict(text=ch_data["title"], font=dict(color=c["text"])), barmode="group", xaxis_tickangle=-45, **_plotly_theme())
        st.plotly_chart(fig, use_container_width=True)


def _compute_monthly_trends(raw_dataframe: list[dict]) -> pd.DataFrame:
    """
    Aggregate raw transactions by calendar month, returning a DataFrame with
    columns: month_label, income, expenses, savings, savings_rate.
    """
    if not raw_dataframe:
        return pd.DataFrame()

    df = pd.DataFrame(raw_dataframe)
    df["date"] = pd.to_datetime(df["date"], infer_datetime_format=True)
    df["month"] = df["date"].dt.to_period("M")

    rows = []
    for period, group in df.groupby("month"):
        # Income
        income_df = group[group["classification"] == "income"]
        income = float(income_df["amount"].sum())

        # Expenses (debit rows are positive spend; credit rows in expense cat are returns)
        expense_df = group[group["classification"] == "expense"].copy()
        expense_df["signed"] = expense_df.apply(
            lambda r: r["amount"] if str(r.get("type", "")).lower().strip() == "debit" else -r["amount"],
            axis=1,
        )
        expenses = float(expense_df["signed"].sum())

        # Refunds reduce expenses
        refund_df = group[group["classification"] == "refund"]
        refund = float(refund_df["amount"].sum())
        net_expenses = max(expenses - refund, 0)

        savings = income - net_expenses
        rate = round(savings / income * 100, 1) if income > 0 else 0.0

        rows.append({
            "month": period,
            "month_label": period.strftime("%b %Y"),
            "income": income,
            "expenses": net_expenses,
            "savings": savings,
            "savings_rate": rate,
        })

    return pd.DataFrame(rows).sort_values("month").reset_index(drop=True)


def _render_mom_dashboard(raw_dataframe: list[dict]):
    """Render live month-on-month savings & spending dashboard."""
    monthly = _compute_monthly_trends(raw_dataframe)
    if monthly.empty:
        return

    st.markdown("## 📊 Monthly Savings & Spending Tracker")

    # ── Delta metrics for the two most recent months ──────────────────────────
    if len(monthly) >= 2:
        curr = monthly.iloc[-1]
        prev = monthly.iloc[-2]

        d_income   = curr["income"]   - prev["income"]
        d_expenses = curr["expenses"] - prev["expenses"]
        d_savings  = curr["savings"]  - prev["savings"]
        d_rate     = curr["savings_rate"] - prev["savings_rate"]

        st.markdown(f"**{curr['month_label']} vs {prev['month_label']}**")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Income",       f"${curr['income']:,.0f}",        f"${d_income:+,.0f}")
        m2.metric("Expenses",     f"${curr['expenses']:,.0f}",      f"${d_expenses:+,.0f}",
                  delta_color="inverse")
        m3.metric("Net Savings",  f"${curr['savings']:,.0f}",       f"${d_savings:+,.0f}")
        m4.metric("Savings Rate", f"{curr['savings_rate']:.1f}%",   f"{d_rate:+.1f}%")
    elif len(monthly) == 1:
        curr = monthly.iloc[0]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Income",       f"${curr['income']:,.0f}")
        m2.metric("Expenses",     f"${curr['expenses']:,.0f}")
        m3.metric("Net Savings",  f"${curr['savings']:,.0f}")
        m4.metric("Savings Rate", f"{curr['savings_rate']:.1f}%")

    # ── Grouped bar chart: Income / Expenses + Savings line ───────────────────
    labels = monthly["month_label"].tolist()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Income",
        x=labels, y=monthly["income"].tolist(),
        marker_color="#10b981", marker_line_width=0,
        text=[f"${v:,.0f}" for v in monthly["income"]],
        textposition="outside",
        textfont=dict(color=c["text"], size=11),
    ))
    fig.add_trace(go.Bar(
        name="Expenses",
        x=labels, y=monthly["expenses"].tolist(),
        marker_color="#ef4444", marker_line_width=0,
        text=[f"${v:,.0f}" for v in monthly["expenses"]],
        textposition="outside",
        textfont=dict(color=c["text"], size=11),
    ))
    fig.add_trace(go.Scatter(
        name="Net Savings",
        x=labels, y=monthly["savings"].tolist(),
        mode="lines+markers+text",
        line=dict(color=c["accent"], width=3),
        marker=dict(size=9, color=c["accent"]),
        text=[f"${v:,.0f}" for v in monthly["savings"]],
        textposition="top center",
        textfont=dict(color=c["text"], size=11),
        yaxis="y",
    ))
    fig.update_layout(
        barmode="group",
        xaxis_title="Month",
        yaxis_title="Amount ($)",
        legend=dict(orientation="h", y=1.1),
        height=420,
        **_plotly_theme(),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Savings-rate trend line ────────────────────────────────────────────────
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=labels, y=monthly["savings_rate"].tolist(),
        mode="lines+markers+text",
        line=dict(color=c["accent_hover"], width=3),
        marker=dict(size=9, color=c["accent_hover"]),
        text=[f"{v:.1f}%" for v in monthly["savings_rate"]],
        textposition="top center",
        textfont=dict(color=c["text"], size=11),
        fill="tozeroy",
        fillcolor=f"rgba(99,102,241,0.12)",
    ))
    fig2.add_hline(y=20, line_dash="dash", line_color=c["text_muted"],
                   annotation_text="20% target", annotation_position="bottom right",
                   annotation_font_color=c["text_muted"])
    fig2.update_layout(
        title=dict(text="Savings Rate Trend (%)", font=dict(color=c["text"])),
        xaxis_title="Month",
        yaxis_title="Savings Rate (%)",
        height=300,
        **_plotly_theme(),
    )
    st.plotly_chart(fig2, use_container_width=True)

    # ── Summary table ──────────────────────────────────────────────────────────
    with st.expander("View month-by-month breakdown"):
        display_df = monthly[["month_label","income","expenses","savings","savings_rate"]].copy()
        display_df.columns = ["Month","Income ($)","Expenses ($)","Savings ($)","Savings Rate (%)"]
        display_df["Income ($)"]   = display_df["Income ($)"].map("${:,.2f}".format)
        display_df["Expenses ($)"] = display_df["Expenses ($)"].map("${:,.2f}".format)
        display_df["Savings ($)"]  = display_df["Savings ($)"].map("${:,.2f}".format)
        display_df["Savings Rate (%)"] = display_df["Savings Rate (%)"].map("{:.1f}%".format)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()


def _render_dashboard(state: FinancialState):
    snapshot = state.get("financial_snapshot") or {}
    health_score = state.get("health_score")
    insights = state.get("financial_insights") or []
    savings_plan = state.get("savings_plan") or {}
    budget_recs = state.get("budget_recommendations") or {}
    charts = state.get("charts") or {}

    # ── Live month-on-month dashboard (shown first) ────────────────────────────
    raw_df = snapshot.get("raw_dataframe") or []
    _render_mom_dashboard(raw_df)

    col1, col2, col3, col4 = st.columns(4)
    with col1: _metric_card("Health Score", f"{health_score}/100", _score_emoji(health_score))
    with col2: _metric_card("Total Income", f"${snapshot.get('total_income', 0):,.2f}", "💵")
    with col3: _metric_card("Net Expenses", f"${snapshot.get('total_expenses', 0):,.2f}", "💸")
    with col4:
        rate = snapshot.get("savings_rate", 0)
        _metric_card("Savings Rate", f"{rate}%", "📈" if rate > 0 else "📉")

    st.divider()

    tab_report, tab_insights, tab_budget, tab_savings, tab_charts = st.tabs([
        "📋 Full Report", "💡 Insights", "📊 Budget", "🏦 Savings", "📈 Charts",
    ])
    with tab_report:
        st.markdown(state.get("final_report") or "No report generated.")
    with tab_insights:
        _render_insights(insights)
    with tab_budget:
        _render_budget(budget_recs)
    with tab_savings:
        _render_savings(savings_plan)
    with tab_charts:
        _render_charts(charts)


# ────────────────────────────────────────────────────────────
# Sidebar
# ────────────────────────────────────────────────────────────
st.sidebar.title("💰 AI Financial Coach")
st.sidebar.markdown("Group 19 — Upload your transactions and get a personalised financial plan.")

# ── API Configuration ────────────────────────────────────────
_MODELS: list[tuple[str, str]] = [
    ("GPT-4o mini (Default)",   "openai/gpt-4o-mini"),
    ("GPT-4o",                  "openai/gpt-4o"),
    ("GPT-4.1",                 "openai/gpt-4.1"),
    ("GPT-5.1",                 "openai/gpt-5.1"),
    ("GPT-120B OSS",            "openai/gpt-120b-oss"),
    ("Claude Opus 4.5",         "anthropic/claude-opus-4-5"),
    ("Claude Sonnet 4.5",       "anthropic/claude-sonnet-4-5"),
    ("Claude Haiku 4.5",        "anthropic/claude-haiku-4-5"),
    ("Llama 3.1 70B Instruct",  "meta-llama/llama-3.1-70b-instruct"),
    ("Gemini 2.0 Flash",        "google/gemini-2.0-flash"),
    ("Mistral 7B Instruct",     "mistralai/mistral-7b-instruct"),
]

with st.sidebar.expander("🔑 API & Model Configuration", expanded=False):
    # ── OpenRouter key ────────────────────────────────────────
    openrouter_key = st.text_input(
        "OpenRouter API Key",
        type="password",
        placeholder="sk-or-...",
        key="openrouter_key_input",
    )

    # ── Tavily key ────────────────────────────────────────────
    tavily_key = st.text_input(
        "Tavily API Key",
        type="password",
        placeholder="tvly-...",
        key="tavily_key_input",
    )

    # ── Model selector ────────────────────────────────────────
    _model_display_names = [name for name, _ in _MODELS]
    _selected_model_idx = st.selectbox(
        "Model",
        options=range(len(_MODELS)),
        format_func=lambda i: _model_display_names[i],
        index=0,
        key="selected_model_idx",
    )
    selected_model_id = _MODELS[_selected_model_idx][1]

    # Persist keys to env so downstream agents can pick them up
    if openrouter_key:
        os.environ["OPENROUTER_API_KEY"] = openrouter_key
    if tavily_key:
        os.environ["TAVILY_API_KEY"] = tavily_key

uploaded_file = st.sidebar.file_uploader(
    "Upload CSV or Excel file", type=["csv", "xlsx", "xls"],
)

user_goals = st.sidebar.text_area(
    "Your financial goals (optional)",
    placeholder="e.g. Pay off credit card debt in 12 months, save for a house",
    height=100,
)

user_location = st.sidebar.text_input(
    "Your location",
    placeholder="e.g. New York, USA or London, UK",
)

run_button = st.sidebar.button("🚀 Analyse My Finances", type="primary", disabled=not uploaded_file)


# ────────────────────────────────────────────────────────────
# Main area
# ────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="app-hero" style="background:linear-gradient(135deg, {c['accent']}, {c['accent_hover']});">
    <h1>💰 AI Financial Coach</h1>
    <p>Upload your transaction history and our multi-agent AI pipeline will generate a comprehensive financial report.</p>
</div>
""", unsafe_allow_html=True)

if not uploaded_file:
    st.info("👈 Upload a CSV or Excel file to get started.")
    st.markdown("""
### Expected file format
| Column | Description |
|--------|-------------|
| `Date` | Transaction date |
| `Description` | Merchant / description |
| `Amount` | Transaction amount (positive values) |
| `Type` | `credit` (money in) or `debit` (money out) |
| `Category` | Spending category (e.g. Groceries, Salary) |
The `Account` column is optional.
**Tip:** Check the `data/` folder in this repo for sample files.
""")
elif run_button:
    suffix = ".csv" if uploaded_file.name.endswith(".csv") else ".xlsx"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    result = None
    try:
        # Streaming progress UI
        st.markdown("### 🔄 Analysing your finances...")
        progress_bar = st.progress(0)
        total_steps = 6

        latest_placeholder = st.empty()
        history_placeholder = st.empty()

        step_log: list[dict] = []
        _status_icons = {"running": "🔄", "done": "✅", "error": "❌"}

        for event in stream_financial_coach(
            raw_data={"file_path": tmp_path},
            user_goals=user_goals,
            location=user_location,
        ):
            if event["type"] == "step_start":
                step_log.append({
                    "status": "running",
                    "icon": event["icon"],
                    "text": f"**{event['label']}** — {event['detail']}",
                })

            elif event["type"] == "step_done":
                # Mark last running step as done
                for s in reversed(step_log):
                    if s["status"] == "running":
                        summary_text = _format_step_summary(event)
                        s["status"] = "done"
                        s["text"] += f" → {summary_text}" if summary_text else " ✅"
                        break
                progress_bar.progress(len([s for s in step_log if s["status"] == "done"]) / total_steps)

            elif event["type"] == "done":
                result = event["result"]
                progress_bar.progress(1.0)

            # Show only the latest message prominently
            if step_log:
                latest = step_log[-1]
                icon = _status_icons.get(latest["status"], "•")
                with latest_placeholder.container():
                    if latest["status"] == "running":
                        st.info(f"{icon} {latest['text']}")
                    else:
                        st.success(f"{icon} {latest['text']}")

            # Full log in a collapsible expander
            if step_log:
                with history_placeholder.container():
                    with st.expander("📋 Full analysis progress", expanded=False):
                        _render_step_log(step_log)

        st.divider()

        if result and result.get("errors"):
            for err in result["errors"]:
                st.warning(err)

        if result and result.get("final_report"):
            _render_dashboard(result)

    except Exception as e:
        st.error(f"❌ Pipeline error: {str(e)}")
    finally:
        os.unlink(tmp_path)
