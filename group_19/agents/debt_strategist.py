import json
from agents.state import FinancialState
from utils.llm_config import get_llm, parse_llm_json, llm_invoke

DEBT_STRATEGIST_PROMPT = """
You are a senior debt strategist. Analyze the provided financial data and
produce a debt payoff plan.  Return ONLY a JSON object with exactly this structure:

{
  "has_debt": <bool>,
  "debt_signals": [
    {
      "category": "<expense category that signals debt, e.g. credit-card-interest, loan, mortgage>",
      "annual_amount": <float>,
      "type": "<credit_card | student_loan | mortgage | auto_loan | personal_loan | other>"
    }
  ],
  "strategy": "<avalanche | snowball | hybrid>",
  "strategy_reason": "<1-sentence explanation of why this strategy fits>",
  "monthly_paydown_target": <float: recommended extra monthly payment>,
  "timeline_months": <int: estimated months to become debt-free>,
  "action_steps": [
    "<specific, numbered action item>"
  ],
  "warnings": [
    "<risk or caveat, e.g. high APR card, variable rate mortgage>"
  ]
}

Guidelines:
  - If there are NO clear debt signals in the data, set has_debt=false,
    keep debt_signals empty, and provide a "maintain debt-free" plan.
  - Mortgage is technically debt but treat it separately — don't flag it as
    urgent unless it exceeds 40% of take-home income.
  - Strategy selection:
    * avalanche  — prioritise highest APR first (best mathematically)
    * snowball   — pay smallest balance first (best psychologically)
    * hybrid     — mix of both
  - monthly_paydown_target should be realistic given the current savings rate.
  - Provide 3-5 action_steps and up to 3 warnings.
"""


def debt_strategist_agent(state: FinancialState) -> dict:
    """
    Debt Strategist Agent
    ---------------------
    - Reads `state['financial_snapshot']`, `state['user_goals']`, and
      `state['financial_insights']` for context.
    - Calls an LLM to identify debt signals and produce a payoff plan.
    - Returns `debt_plan` and appends errors.
    """

    errors = list(state.get("errors", []))
    snapshot = state.get("financial_snapshot")

    if snapshot is None:
        errors.append("[debt_strategist] No financial_snapshot available.")
        return {
            "debt_plan": None,
            "errors": errors,
            "current_agent": "debt_strategist",
        }

    user_goals = state.get("user_goals", "").strip()
    insights = state.get("financial_insights", [])

    # Build context for the LLM
    analysis_context = {
        "total_income": snapshot.get("total_income"),
        "total_expenses": snapshot.get("total_expenses"),
        "net_savings": snapshot.get("net_savings"),
        "savings_rate": snapshot.get("savings_rate"),
        "expense_by_category": snapshot.get("expense_by_category", {}),
        "income_sources": snapshot.get("income_sources", {}),
        "user_goals": user_goals if user_goals else "(none specified)",
        "prior_insights": [
            {"category": i.get("category"), "finding": i.get("finding")}
            for i in insights
        ] if insights else "(no prior insights)",
    }

    llm = get_llm()
    messages = [
        ("system", DEBT_STRATEGIST_PROMPT),
        ("human", json.dumps(analysis_context, indent=2, default=str)),
    ]

    try:
        response = llm_invoke(llm, messages)
        debt_plan = parse_llm_json(response.content)

        # Basic validation
        if "has_debt" not in debt_plan:
            errors.append("[debt_strategist] LLM response missing 'has_debt' field.")
            debt_plan["has_debt"] = False
        if "strategy" not in debt_plan:
            errors.append("[debt_strategist] LLM response missing 'strategy' field.")
            debt_plan["strategy"] = "avalanche"
            debt_plan["strategy_reason"] = "Default strategy."
        if "action_steps" not in debt_plan or not debt_plan["action_steps"]:
            debt_plan["action_steps"] = ["Monitor finances and avoid taking on new debt."]

    except json.JSONDecodeError as e:
        errors.append(f"[debt_strategist] Failed to parse LLM response as JSON: {e}")
        return {
            "debt_plan": None,
            "errors": errors,
            "current_agent": "debt_strategist",
        }
    except Exception as e:
        errors.append(f"[debt_strategist] Unexpected error: {e}")
        return {
            "debt_plan": None,
            "errors": errors,
            "current_agent": "debt_strategist",
        }

    return {
        "debt_plan": debt_plan,
        "errors": errors,
        "current_agent": "debt_strategist",
    }
