import json
from agents.state import FinancialState
from utils.llm_config import get_llm, parse_llm_json, llm_invoke

BUDGET_ADVISOR_PROMPT = """You are a senior budget advisor. Analyze the financial data and return budget allocations.

IMPORTANT: Respond with ONLY a raw JSON object. No markdown, no code fences, no explanation text before or after.

Required JSON structure (fill in real numbers from the data):
{"budget_period":"monthly","allocations":[{"category":"<name>","current_avg":<float>,"recommended":<float>,"variance_pct":<float>,"note":"<string>"}],"total_budgeted":<float>,"surplus":<float>,"alerts":[{"category":"<name>","type":"overspending","message":"<string>"}],"monthly_summary":"<string>"}

Rules:
- Include every expense category in the data.
- variance_pct = (current_avg - recommended) / recommended * 100  (positive = overspending).
- Aim for 5-15% reductions on high-spend categories.
- surplus = total_income - total_budgeted.
- alerts: flag only categories that are unusually high (>30% of expenses) or erratic.
- monthly_summary: 2-3 sentences max.

Output the JSON object only. Start your response with { and end with }."""


def budget_advisor_agent(state: FinancialState) -> dict:
    errors = list(state.get("errors", []))
    snapshot = state.get("financial_snapshot")

    if snapshot is None:
        errors.append("[budget_advisor] No financial_snapshot available.")
        return {"budget_recommendations": None, "errors": errors, "current_agent": "budget_advisor"}

    user_goals = state.get("user_goals", "").strip()
    insights = state.get("financial_insights", [])
    debt_plan = state.get("debt_plan")
    savings_plan = state.get("savings_plan")

    analysis_context = {
        "total_income": snapshot.get("total_income"),
        "total_expenses": snapshot.get("total_expenses"),
        "net_savings": snapshot.get("net_savings"),
        "savings_rate": snapshot.get("savings_rate"),
        "expense_by_category": snapshot.get("expense_by_category", {}),
        "user_goals": user_goals if user_goals else "(none specified)",
        "prior_insights": [
            {"category": i.get("category"), "finding": i.get("finding"), "severity": i.get("severity")}
            for i in (insights or [])
        ],
        "debt_paydown": debt_plan.get("monthly_paydown_target", 0) if debt_plan else 0,
        "savings_contributions": _sum_savings_contributions(savings_plan),
    }

    llm = get_llm()
    messages = [
        ("system", BUDGET_ADVISOR_PROMPT),
        ("human", json.dumps(analysis_context, indent=2)),
    ]

    budget_recommendations = None
    try:
        response = llm_invoke(llm, messages)
        budget_recommendations = parse_llm_json(response.content)

        if "allocations" not in budget_recommendations or not budget_recommendations["allocations"]:
            # LLM parsed but returned empty allocations — build from data as fallback
            budget_recommendations = _fallback_budget(snapshot)
            errors.append("[budget_advisor] LLM returned empty allocations — used data-driven fallback.")

    except (json.JSONDecodeError, ValueError):
        # parse_llm_json exhausted all attempts — build directly from expense data
        budget_recommendations = _fallback_budget(snapshot)
        errors.append("[budget_advisor] LLM response unparseable — used data-driven fallback.")
    except Exception as e:
        budget_recommendations = _fallback_budget(snapshot)
        errors.append(f"[budget_advisor] LLM error ({e}) — used data-driven fallback.")

    return {
        "budget_recommendations": budget_recommendations,
        "errors": errors,
        "current_agent": "budget_advisor",
    }


def _fallback_budget(snapshot: dict) -> dict:
    """Build budget recommendations directly from expense_by_category without LLM."""
    expense_by_cat = snapshot.get("expense_by_category") or {}
    total_income = float(snapshot.get("total_income") or 0)

    allocations = []
    for cat, current in expense_by_cat.items():
        current = float(current)
        if current <= 0:
            continue
        # Recommend a 10% reduction on each category
        recommended = round(current * 0.90, 2)
        variance_pct = round((current - recommended) / recommended * 100, 1)
        allocations.append({
            "category": cat,
            "current_avg": round(current, 2),
            "recommended": recommended,
            "variance_pct": variance_pct,
            "note": "Suggested 10% reduction based on spending data.",
        })

    total_budgeted = round(sum(a["recommended"] for a in allocations), 2)
    surplus = round(total_income - total_budgeted, 2)

    # Flag the single largest expense category
    alerts = []
    if allocations:
        top = max(allocations, key=lambda a: a["current_avg"])
        alerts.append({
            "category": top["category"],
            "type": "overspending",
            "message": f"{top['category']} is your largest expense at ${top['current_avg']:,.0f}. Consider reducing it.",
        })

    return {
        "budget_period": "monthly",
        "allocations": allocations,
        "total_budgeted": total_budgeted,
        "surplus": surplus,
        "alerts": alerts,
        "monthly_summary": (
            f"Based on your spending data, a 10% reduction across all categories would "
            f"save ${round(sum(a['current_avg'] - a['recommended'] for a in allocations), 0):,.0f}/month "
            f"and give you a monthly surplus of ${surplus:,.0f}."
        ),
    }


def _sum_savings_contributions(savings_plan: dict | None) -> float:
    if not savings_plan:
        return 0.0
    total = 0.0
    ef = savings_plan.get("emergency_fund", {})
    total += ef.get("monthly_contribution", 0)
    for goal in savings_plan.get("savings_goals", []):
        total += goal.get("monthly_contribution", 0)
    return total
