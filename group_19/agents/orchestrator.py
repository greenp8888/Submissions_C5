from langgraph.graph import StateGraph, END
from agents.state import FinancialState
from agents.document_ingestion import document_ingestion_agent
from agents.financial_analyzer import financial_analyzer_agent
from agents.debt_strategist import debt_strategist_agent
from agents.savings_strategy import savings_strategy_agent
from agents.budget_advisor import budget_advisor_agent
from agents.report_generator import report_generator_agent

# Human-readable step descriptions
_STEP_META = {
    "document_ingestion": {
        "icon": "📂",
        "label": "Ingesting & validating financial data",
        "detail": "Parsing transactions, classifying income/expenses/transfers",
    },
    "financial_analyzer": {
        "icon": "🧠",
        "label": "Analysing financial health",
        "detail": "Computing health score, generating key insights",
    },
    "debt_strategist": {
        "icon": "💳",
        "label": "Building debt strategy",
        "detail": "Detecting debt signals, recommending payoff approach",
    },
    "savings_strategy": {
        "icon": "🏦",
        "label": "Designing savings plan",
        "detail": "Setting emergency fund target & savings goals",
    },
    "budget_advisor": {
        "icon": "📊",
        "label": "Optimising budget",
        "detail": "Allocating category budgets, flagging overspending",
    },
    "report_generator": {
        "icon": "📋",
        "label": "Generating final report",
        "detail": "Compiling insights, plans & charts into a report",
    },
}


def build_financial_coach_graph():
    """Builds and compiles the multi-agent LangGraph workflow."""

    graph = StateGraph(FinancialState)

    # Register all agents as nodes
    graph.add_node("document_ingestion",  document_ingestion_agent)
    graph.add_node("financial_analyzer",  financial_analyzer_agent)
    graph.add_node("debt_strategist",     debt_strategist_agent)
    graph.add_node("savings_strategy",    savings_strategy_agent)
    graph.add_node("budget_advisor",      budget_advisor_agent)
    graph.add_node("report_generator",    report_generator_agent)

    # Define the flow (sequential pipeline)
    graph.set_entry_point("document_ingestion")
    graph.add_edge("document_ingestion",  "financial_analyzer")
    graph.add_edge("financial_analyzer",  "debt_strategist")
    graph.add_edge("debt_strategist",     "savings_strategy")
    graph.add_edge("savings_strategy",    "budget_advisor")
    graph.add_edge("budget_advisor",      "report_generator")
    graph.add_edge("report_generator",    END)

    return graph.compile()

# Singleton graph instance
financial_coach = build_financial_coach_graph()


def run_financial_coach(raw_data: dict, user_goals: str = "", location: str = "") -> FinancialState:
    """Entry point to run the full agent pipeline."""
    initial_state = FinancialState(
        raw_data=raw_data,
        user_goals=user_goals,
        location=location,
        financial_snapshot=None,
        health_score=None,
        financial_insights=None,
        debt_plan=None,
        savings_plan=None,
        budget_recommendations=None,
        final_report=None,
        charts=None,
        errors=[],
        current_agent="starting"
    )
    result = financial_coach.invoke(initial_state)
    return result


def stream_financial_coach(raw_data: dict, user_goals: str = "", location: str = ""):
    """
    Generator that yields step progress dicts and the final result.

    Yields:
        {"type": "step_start", "agent": "...", "icon": "...",
         "label": "...", "detail": "..."}
        {"type": "step_done",   "agent": "...", "summary": {...}}
        {"type": "done", "result": FinancialState}
    """
    initial_state = FinancialState(
        raw_data=raw_data,
        user_goals=user_goals,
        location=location,
        financial_snapshot=None,
        health_score=None,
        financial_insights=None,
        debt_plan=None,
        savings_plan=None,
        budget_recommendations=None,
        final_report=None,
        charts=None,
        errors=[],
        current_agent="starting"
    )

    # Accumulate state from stream updates so we don't re-invoke
    accumulated = dict(initial_state)

    try:
        for step in financial_coach.stream(initial_state, stream_mode="updates"):
            for node_name, updates in step.items():
                meta = _STEP_META.get(node_name, {"icon": "⚙️", "label": node_name, "detail": ""})

                yield {
                    "type": "step_start",
                    "agent": node_name,
                    "icon": meta["icon"],
                    "label": meta["label"],
                    "detail": meta["detail"],
                }

                # Merge updates into accumulated state
                accumulated.update(updates)

                snapshot_summary = {}
                if node_name == "document_ingestion":
                    snap = updates.get("financial_snapshot") or {}
                    snapshot_summary = {
                        "total_income": snap.get("total_income"),
                        "total_expenses": snap.get("total_expenses"),
                        "savings_rate": snap.get("savings_rate"),
                        "transaction_count": snap.get("transaction_count"),
                    }
                elif node_name == "financial_analyzer":
                    snapshot_summary = {
                        "health_score": updates.get("health_score"),
                        "insights_count": len(updates.get("financial_insights") or []),
                    }
                elif node_name == "debt_strategist":
                    dp = updates.get("debt_plan") or {}
                    snapshot_summary = {
                        "has_debt": dp.get("has_debt"),
                        "strategy": dp.get("strategy"),
                    }
                elif node_name == "savings_strategy":
                    sp = updates.get("savings_plan") or {}
                    snapshot_summary = {
                        "emergency_target": (sp.get("emergency_fund") or {}).get("target_amount"),
                        "goals_count": len(sp.get("savings_goals") or []),
                    }
                elif node_name == "budget_advisor":
                    br = updates.get("budget_recommendations") or {}
                    snapshot_summary = {
                        "categories_budgeted": len(br.get("allocations") or []),
                        "surplus": br.get("surplus"),
                    }
                elif node_name == "report_generator":
                    report = updates.get("final_report") or ""
                    snapshot_summary = {"report_length": len(report)}

                yield {
                    "type": "step_done",
                    "agent": node_name,
                    "icon": meta["icon"],
                    "summary": snapshot_summary,
                    "errors": updates.get("errors") or [],
                }

    except Exception as e:
        # An agent crashed — record the error and continue to emit done with partial results
        errs = accumulated.get("errors") or []
        errs.append(f"[pipeline] Unexpected crash: {e}")
        accumulated["errors"] = errs

    # Always emit done — even with partial results — so the client can render what it has
    yield {"type": "done", "result": accumulated}