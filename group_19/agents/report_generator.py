import json
import textwrap
from agents.state import FinancialState
from utils.llm_config import get_llm, parse_llm_json, llm_invoke

REPORT_GENERATOR_PROMPT = """
You are a financial report writer. Combine all prior agent outputs into a
clear, professional, human-readable financial report in Markdown format.

Include these sections:
  1. **Financial Health Score** — score out of 100 with a 1-line label
     (Excellent / Good / Fair / Below Average / Poor).
  2. **Income & Expense Overview** — key totals and top 3 expense categories.
  3. **Key Insights** — bullet-point findings from the financial analyzer,
     grouped by severity (critical → warning → info → positive).
  4. **Debt Analysis** — debt status, strategy, and action steps.
  5. **Savings Plan** — emergency fund, savings goals, and quick wins.
  6. **Budget Recommendations** — allocation table and alerts.
  7. **Next Steps** — 3-5 prioritised actions combining all agent advice.

The report should:
  - Be concise (aim for ~600-800 words).
  - Use the user's name or "you" — conversational but professional.
  - Reference specific dollar amounts from the data.
  - If the user specified goals, explicitly address them.

Return a JSON object:
{ "report_markdown": "<the full markdown report as a single string>" }
"""


def report_generator_agent(state: FinancialState) -> dict:
    """
    Report Generator Agent
    ----------------------
    - Reads ALL prior agent outputs from state.
    - Calls an LLM to compose a consolidated Markdown report.
    - Also generates chart data for the UI.
    - Returns `final_report` and `charts`.
    """

    errors = list(state.get("errors", []))
    snapshot = state.get("financial_snapshot")

    if snapshot is None:
        errors.append("[report_generator] No financial_snapshot available.")
        return {
            "final_report": None,
            "charts": None,
            "errors": errors,
            "current_agent": "report_generator",
        }

    user_goals = state.get("user_goals", "").strip()
    health_score = state.get("health_score")
    insights = state.get("financial_insights") or []
    debt_plan = state.get("debt_plan") or {}
    savings_plan = state.get("savings_plan") or {}
    budget_recs = state.get("budget_recommendations") or {}

    context = {
        "financial_snapshot": snapshot,
        "health_score": health_score,
        "financial_insights": insights,
        "debt_plan": debt_plan,
        "savings_plan": savings_plan,
        "budget_recommendations": budget_recs,
        "user_goals": user_goals if user_goals else "(none specified)",
    }

    llm = get_llm()
    messages = [
        ("system", REPORT_GENERATOR_PROMPT),
        ("human", json.dumps(context, indent=2, default=str)),
    ]

    try:
        response = llm_invoke(llm, messages)
        raw_content = response.content.strip()

        # Try structured JSON first, fall back to treating entire response as markdown
        try:
            parsed = parse_llm_json(raw_content)
            final_report = parsed.get("report_markdown", "")
            if not final_report:
                # LLM returned JSON but without the expected key — use raw as markdown
                final_report = raw_content
        except (ValueError, Exception):
            # LLM returned raw markdown (no JSON wrapper) — use it directly
            final_report = raw_content

        if not final_report:
            errors.append("[report_generator] Empty report from LLM.")
            final_report = _fallback_report(snapshot, health_score, insights)

    except Exception as e:
        errors.append(f"[report_generator] LLM call failed: {e}")
        final_report = _fallback_report(snapshot, health_score, insights)

    # Build chart data — wrapped so a chart error never kills the whole pipeline
    try:
        charts = _build_charts(snapshot, insights, budget_recs, savings_plan)
    except Exception as e:
        errors.append(f"[report_generator] Chart build failed: {e}")
        charts = {}

    return {
        "final_report": final_report,
        "charts": charts,
        "errors": errors,
        "current_agent": "report_generator",
    }


def _build_charts(snapshot: dict, insights: list, budget_recs: dict,
                  savings_plan: dict) -> dict:
    """Build Plotly-compatible chart data as JSON-serialisable dicts."""
    charts = {}

    # 1. Expense breakdown (pie chart data)
    exp_by_cat = snapshot.get("expense_by_category", {})
    if exp_by_cat:
        charts["expense_breakdown"] = {
            "type": "pie",
            "labels": list(exp_by_cat.keys()),
            "values": [round(v, 2) for v in exp_by_cat.values()],
            "title": "Expenses by Category",
        }

    # 2. Income vs Expenses (bar)
    charts["income_vs_expense"] = {
        "type": "bar",
        "categories": ["Total Income", "Net Expenses", "Net Savings"],
        "values": [
            round(snapshot.get("total_income", 0), 2),
            round(snapshot.get("total_expenses", 0), 2),
            round(snapshot.get("net_savings", 0), 2),
        ],
        "title": "Income vs Expenses",
    }

    # 3. Budget vs Current (grouped bar) if budget recs exist
    if budget_recs and budget_recs.get("allocations"):
        allocs = budget_recs["allocations"]
        charts["budget_comparison"] = {
            "type": "grouped_bar",
            "categories": [a["category"] for a in allocs],
            "current": [round(a.get("current_avg", 0), 2) for a in allocs],
            "recommended": [round(a.get("recommended", 0), 2) for a in allocs],
            "title": "Current vs Recommended Budget",
        }

    return charts


def _fallback_report(snapshot: dict, health_score: float | None,
                     insights: list) -> str:
    """Generate a plain-text report if the LLM fails."""
    label = _score_label(health_score)
    lines = [
        "# Financial Report",
        "",
        f"**Health Score:** {health_score}/100 ({label})",
        "",
        f"- **Income:** ${snapshot.get('total_income', 0):,.2f}",
        f"- **Expenses:** ${snapshot.get('total_expenses', 0):,.2f}",
        f"- **Net Savings:** ${snapshot.get('net_savings', 0):,.2f}",
        f"- **Savings Rate:** {snapshot.get('savings_rate', 0)}%",
        "",
        "## Insights",
        "",
    ]
    for i in (insights or []):
        lines.append(f"- **[{i.get('severity','')}]** {i.get('finding','')}")
    lines.append("")
    return "\n".join(lines)


def _score_label(score: float | None) -> str:
    if score is None:
        return "Unknown"
    if score >= 90:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 50:
        return "Fair"
    if score >= 30:
        return "Below Average"
    return "Poor"
