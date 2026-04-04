from typing import Dict, Any


def analyze_savings(
    monthly_income: float,
    total_expenses: float,
    primary_goal: str,
) -> Dict[str, Any]:
    """Analyze savings position using monthly income, expenses, and user goal."""
    if monthly_income <= 0:
        return {
            "surplus": 0.0,
            "savings_rate": 0.0,
            "recommended_savings_target": 0.0,
            "strategy_level": "Insufficient data",
            "strategy_message": (
                "Monthly income is zero or unavailable, so a reliable savings strategy cannot be created yet."
            ),
        }

    surplus = monthly_income - total_expenses
    savings_rate = round((surplus / monthly_income) * 100, 1) if monthly_income > 0 else 0.0
    recommended_savings_target = round(max(monthly_income * 0.20, 0), 2)

    if surplus < 0:
        strategy_level = "Critical"
        strategy_message = (
            f"Your current monthly expenses exceed income by ₹{abs(surplus):,.0f}. "
            f"For the goal '{primary_goal}', the immediate focus should be expense reduction, "
            "cutting discretionary spending, and pausing non-essential outflows before savings allocation."
        )
    elif savings_rate < 10:
        strategy_level = "Needs improvement"
        strategy_message = (
            f"Your estimated monthly surplus is ₹{surplus:,.0f}, with a savings rate of {savings_rate:.1f}%. "
            f"For the goal '{primary_goal}', increase fixed monthly savings and reduce flexible categories "
            "like shopping, food delivery, and entertainment."
        )
    elif savings_rate < 20:
        strategy_level = "Moderate"
        strategy_message = (
            f"Your estimated monthly surplus is ₹{surplus:,.0f}, with a savings rate of {savings_rate:.1f}%. "
            f"For the goal '{primary_goal}', you are on a reasonable track, but improving savings toward "
            f"₹{recommended_savings_target:,.0f} per month would strengthen resilience."
        )
    else:
        strategy_level = "Strong"
        strategy_message = (
            f"Your estimated monthly surplus is ₹{surplus:,.0f}, with a savings rate of {savings_rate:.1f}%. "
            f"For the goal '{primary_goal}', you are in a strong position. Maintain discipline and direct "
            "part of the surplus toward debt reduction, emergency funds, or goal-based investing."
        )

    return {
        "surplus": round(surplus, 2),
        "savings_rate": round(savings_rate, 1),
        "recommended_savings_target": recommended_savings_target,
        "strategy_level": strategy_level,
        "strategy_message": strategy_message,
    }


def format_savings_output(savings_result: Dict[str, Any]) -> str:
    """Format savings strategy result into app-friendly text."""
    if not savings_result:
        return "Savings strategy is unavailable."

    return savings_result.get("strategy_message", "Savings strategy is unavailable.")
