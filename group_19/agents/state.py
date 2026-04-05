from typing import TypedDict, List, Dict, Any, Optional


class FinancialState(TypedDict):
    """
    State schema for the Financial Coach multi-agent LangGraph workflow.
    Each agent reads and writes specific fields as data flows through the pipeline.
    """

    raw_data: Dict[str, Any]
    """Parsed financial data from the uploaded file (output of file_parser)."""

    user_goals: str
    """Free-text goals provided by the user (e.g., 'pay off credit card debt faster')."""

    location: str
    """User's location (city/country) used to tailor region-specific financial advice."""

    financial_snapshot: Optional[Dict[str, Any]]
    """Structured summary: income, expenses, savings rate, category breakdown."""

    health_score: Optional[float]
    """Numerical financial health score (0-100)."""

    financial_insights: Optional[List[Dict[str, Any]]]
    """List of insight objects with findings and recommendations."""

    debt_plan: Optional[Dict[str, Any]]
    """Debt analysis: payoff strategy, timeline, prioritized debts."""

    savings_plan: Optional[Dict[str, Any]]
    """Savings recommendations: targets, timelines, suggested amounts."""

    budget_recommendations: Optional[Dict[str, Any]]
    """Budget allocations by category with actionable guidance."""

    final_report: Optional[str]
    """Human-readable consolidated report combining all agent outputs."""

    charts: Optional[Dict[str, Any]]
    """Plotly chart figures (encoded as JSON/dict) for the UI."""

    errors: List[str]
    """Accumulated error messages from any agent in the pipeline."""

    current_agent: str
    """Tracks which agent is currently executing (useful for debugging/logging)."""
