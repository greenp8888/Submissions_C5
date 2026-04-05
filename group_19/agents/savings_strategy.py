import json
import os
from agents.state import FinancialState
from utils.llm_config import get_llm, parse_llm_json, llm_invoke
from tavily import TavilyClient

SAVINGS_STRATEGIST_PROMPT = """
You are a senior savings strategist. Analyze the provided financial data and
produce a personalized savings plan.  Return ONLY a JSON object with exactly
this structure:

{
  "emergency_fund": {
    "target_amount": <float: 3-6 months of expenses>,
    "current_estimate": <float: net_savings * 0.5 as rough proxy, or 0 if unknown>,
    "months_to_fund": <int>,
    "monthly_contribution": <float>
  },
  "savings_goals": [
    {
      "goal": "<short_term | mid_term | long_term | retirement>",
      "label": "<descriptive name>",
      "target_amount": <float>,
      "timeline_months": <int>,
      "monthly_contribution": <float>
    }
  ],
  "recommended_rate": <float: suggested savings rate %>,
  "account_suggestions": [
    "<e.g. high-yield savings, 401k match, Roth IRA, index fund>"
  ],
  "quick_wins": [
    "<specific actionable tip to free up cash>"
  ]
}

Guidelines:
  - emergency_fund target should be 3-6 months of net expenses.
  - recommended_rate should reflect current financial reality
    (don't suggest 40% savings when the user is deficit spending).
  - Provide 2-4 savings_goals, each with realistic monthly amounts
    that together don't exceed available net savings.
  - Include 3-5 quick_wins derived from the expense data.
  - If location is provided, tailor account_suggestions and advice to
    financial products available in that region.
"""


def _search_bank_offers(location: str) -> list[dict]:
    """
    Use Tavily to search for top high-interest savings account offers
    relevant to the user's location. Returns a list of result dicts with
    title, url, and content keys.

    Web search requires a valid Tavily API key set as the TAVILY_API_KEY
    environment variable. Get a free key at https://tavily.com and add it
    to your .env file:  TAVILY_API_KEY=tvly-...
    """
    try:
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key or api_key == "your-tavily-api-key-here":
            return [
                {
                    "title": "Web search unavailable",
                    "url": "",
                    "snippet": (
                        "Live bank offer search is disabled. To enable it, set a valid "
                        "TAVILY_API_KEY in your environment (e.g. in your .env file). "
                        "You can get a free key at https://tavily.com."
                    ),
                }
            ]

        client = TavilyClient(api_key=api_key)

        location_clause = f"in {location}" if location.strip() else ""
        query = f"best high interest savings accounts {location_clause} 2024 top rates banks"

        response = client.search(
            query=query,
            search_depth="basic",
            max_results=5,
            include_answer=False,
        )

        results = []
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", "")[:300],
            })
        return results

    except ImportError:
        return []
    except Exception:
        return []


def savings_strategy_agent(state: FinancialState) -> dict:
    """
    Savings Strategy Agent
    ----------------------
    - Reads `state['financial_snapshot']`, `state['user_goals']`,
      `state['financial_insights']`, `state['debt_plan']`, and `state['location']`.
    - Calls an LLM to produce a savings plan with emergency fund,
      goal targets, and actionable tips.
    - After generating the plan, calls Tavily to fetch top high-interest
      savings account offers for the user's location and appends them as
      `bank_offers` inside the savings_plan.
    - Returns `savings_plan` and appends errors.
    """

    errors = list(state.get("errors", []))
    snapshot = state.get("financial_snapshot")

    if snapshot is None:
        errors.append("[savings_strategy] No financial_snapshot available.")
        return {
            "savings_plan": None,
            "errors": errors,
            "current_agent": "savings_strategy",
        }

    user_goals = state.get("user_goals", "").strip()
    location = state.get("location", "").strip()
    insights = state.get("financial_insights", [])
    debt_plan = state.get("debt_plan")

    analysis_context = {
        "total_income": snapshot.get("total_income"),
        "total_expenses": snapshot.get("total_expenses"),
        "net_savings": snapshot.get("net_savings"),
        "savings_rate": snapshot.get("savings_rate"),
        "expense_by_category": snapshot.get("expense_by_category", {}),
        "income_sources": snapshot.get("income_sources", {}),
        "user_goals": user_goals if user_goals else "(none specified)",
        "location": location if location else "(not specified)",
        "prior_insights": [
            {"category": i.get("category"), "finding": i.get("finding")}
            for i in insights
        ] if insights else "(no prior insights)",
        "debt_status": debt_plan.get("has_debt", None) if debt_plan else None,
        "debt_paydown": debt_plan.get("monthly_paydown_target", 0) if debt_plan else 0,
    }

    llm = get_llm()
    messages = [
        ("system", SAVINGS_STRATEGIST_PROMPT),
        ("human", json.dumps(analysis_context, indent=2, default=str)),
    ]

    try:
        response = llm_invoke(llm, messages)
        savings_plan = parse_llm_json(response.content)

        for key in ("emergency_fund", "savings_goals", "recommended_rate"):
            if key not in savings_plan:
                errors.append(f"[savings_strategy] Missing '{key}' in LLM response.")

    except (json.JSONDecodeError, ValueError) as e:
        errors.append(f"[savings_strategy] Failed to parse LLM response as JSON: {e}")
        return {
            "savings_plan": None,
            "errors": errors,
            "current_agent": "savings_strategy",
        }
    except Exception as e:
        errors.append(f"[savings_strategy] Unexpected error: {e}")
        return {
            "savings_plan": None,
            "errors": errors,
            "current_agent": "savings_strategy",
        }

    # Search for top bank offers via Tavily
    bank_offers = _search_bank_offers(location)
    savings_plan["bank_offers"] = bank_offers

    return {
        "savings_plan": savings_plan,
        "errors": errors,
        "current_agent": "savings_strategy",
    }
