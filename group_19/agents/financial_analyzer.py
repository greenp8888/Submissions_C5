import json
from agents.state import FinancialState
from utils.llm_config import get_llm, parse_llm_json, llm_invoke

FINANCIAL_ANALYZER_PROMPT = """
You are a senior financial analyst. Analyze the provided financial snapshot and
return a JSON object with exactly this structure:

{
  "health_score": <float 0-100>,
  "insights": [
    {
      "category": "<string: e.g. savings, spending, income, debt, investment>",
      "finding": "<clear, specific observation from the data>",
      "severity": "<critical | warning | info | positive>",
      "recommendation": "<actionable advice>"
    }
  ]
}

Guidelines for health_score:
  90-100  Excellent — high savings rate (>30 %), diversified income, low debt burden
  70-89   Good — solid savings rate (15-30 %), manageable expenses
  50-69   Fair — savings rate 0-15 % or one concerning expense area
  30-49   Below average — negative savings or high discretionary spending
  0-29    Poor — significant deficit spending, no savings, or extreme debt signals

Guidelines for insights:
  - Produce 4-8 insights covering different angles (savings rate, top expense
    categories, income diversification, anomalies).
  - Each insight MUST reference a concrete number from the data.
  - severity helps the UI highlight urgent issues.
  - Keep recommendations to 1-2 sentences, actionable and specific.
"""


def financial_analyzer_agent(state: FinancialState) -> dict:
    """
    Financial Analyzer Agent
    -----------------------
    - Reads `state['financial_snapshot']` and `state['user_goals']`.
    - Calls an LLM to compute a health score (0-100) and generate insights.
    - Returns `health_score`, `financial_insights`, and appends errors.
    """

    errors = list(state.get("errors", []))
    snapshot = state.get("financial_snapshot")

    if snapshot is None:
        errors.append("[financial_analyzer] No financial_snapshot available. "
                      "Document ingestion may have failed.")
        return {
            "health_score": None,
            "financial_insights": None,
            "errors": errors,
            "current_agent": "financial_analyzer",
        }

    user_goals = state.get("user_goals", "").strip()

    # Prepare context for the LLM
    analysis_context = {
        "total_income": snapshot.get("total_income"),
        "total_expenses": snapshot.get("total_expenses"),
        "net_savings": snapshot.get("net_savings"),
        "savings_rate": snapshot.get("savings_rate"),
        "expense_by_category": snapshot.get("expense_by_category", {}),
        "income_sources": snapshot.get("income_sources", {}),
        "transaction_count": snapshot.get("transaction_count"),
        "refund_amount": snapshot.get("refund_amount"),
        "transfer_amount": snapshot.get("transfer_amount"),
        "user_goals": user_goals if user_goals else "(none specified)",
    }

    llm = get_llm()
    messages = [
        ("system", FINANCIAL_ANALYZER_PROMPT),
        ("human", json.dumps(analysis_context, indent=2, default=str)),
    ]

    try:
        response = llm_invoke(llm, messages)
        result = parse_llm_json(response.content)

        health_score = float(result.get("health_score", 0))
        financial_insights = result.get("insights", [])

        # Validate
        if not (0 <= health_score <= 100):
            errors.append(f"[financial_analyzer] Invalid health_score: {health_score}. Clamping to 0-100.")
            health_score = max(0.0, min(100.0, health_score))

        if not isinstance(financial_insights, list) or len(financial_insights) == 0:
            errors.append("[financial_analyzer] No insights returned by LLM.")
            financial_insights = []

    except json.JSONDecodeError as e:
        errors.append(f"[financial_analyzer] Failed to parse LLM response as JSON: {e}")
        return {
            "health_score": None,
            "financial_insights": None,
            "errors": errors,
            "current_agent": "financial_analyzer",
        }
    except Exception as e:
        errors.append(f"[financial_analyzer] Unexpected error: {e}")
        return {
            "health_score": None,
            "financial_insights": None,
            "errors": errors,
            "current_agent": "financial_analyzer",
        }

    return {
        "health_score": round(health_score, 1),
        "financial_insights": financial_insights,
        "errors": errors,
        "current_agent": "financial_analyzer",
    }
