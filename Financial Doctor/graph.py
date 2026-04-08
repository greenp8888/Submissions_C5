"""
FinanceDoctor — LangGraph Multi-Agent Orchestration (Layer 3)
==============================================================
5-node graph: Orchestrator → (Debt Analyzer | Savings Strategy | Budget Advisor | Action Planner) → END

Each specialist agent is a ReAct agent with two tools:
  1. search_financial_data — RAG retrieval from LanceDB
  2. tavily_search — live web search for current rates/data
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, Optional, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import create_react_agent

from config import (
    ORCHESTRATOR_SYSTEM_PROMPT,
    DEBT_AGENT_SYSTEM_PROMPT,
    SAVINGS_AGENT_SYSTEM_PROMPT,
    BUDGET_AGENT_SYSTEM_PROMPT,
    ACTION_AGENT_SYSTEM_PROMPT,
)


# ─────────────────────────────────────────────
# 1. STATE
# ─────────────────────────────────────────────

class FinanceDoctorState(TypedDict):
    """Shared state flowing through every node."""
    messages: Annotated[list[BaseMessage], operator.add]
    financial_data_summary: str   # brief summary of uploaded data
    route_decision: str           # which agent to route to


# ─────────────────────────────────────────────
# 2. HELPER — build financial data block
# ─────────────────────────────────────────────

def _build_data_block(state: FinanceDoctorState) -> str:
    summary = state.get("financial_data_summary", "")
    if summary and summary.strip():
        return (
            "\n--- USER'S FINANCIAL DATA SUMMARY ---\n"
            f"{summary}\n"
            "--- END FINANCIAL DATA ---\n"
            "Use the search_financial_data tool to find specific details from this data."
        )
    return "\n(No financial data uploaded by the user yet.)"


# ─────────────────────────────────────────────
# 3. GRAPH BUILDER
# ─────────────────────────────────────────────

def build_graph(
    openrouter_api_key: str,
    tavily_api_key: str,
    model_name: str = "google/gemini-2.0-flash-exp:free",
    rag_pipeline=None,
):
    """
    Construct and compile the 5-node FinanceDoctor LangGraph.

    Args:
        openrouter_api_key: OpenRouter API key
        tavily_api_key: Tavily API key for web search
        model_name: OpenRouter model identifier
        rag_pipeline: RAGPipeline instance (optional, for vector search)

    Returns:
        Compiled LangGraph ready for .invoke()
    """
    import os
    os.environ["TAVILY_API_KEY"] = tavily_api_key

    # ── LLM via OpenRouter ─────────────────────────
    llm = ChatOpenAI(
        model=model_name,
        openai_api_key=openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.3,
        max_tokens=4096,
    )

    # ── Tools ──────────────────────────────────────
    tavily_tool = TavilySearch(max_results=3, topic="finance")

    def _rag_search(query: str) -> str:
        """Search the user's uploaded financial documents."""
        if rag_pipeline is None or not rag_pipeline.is_ready:
            return "No financial data has been uploaded yet. Ask the user to upload a bank statement or financial document."
        results = rag_pipeline.query(query, top_k=5)
        if not results:
            return "No relevant financial data found for this query in the uploaded documents."
        return "\n\n---\n\n".join(results)

    rag_tool = Tool(
        name="search_financial_data",
        description=(
            "Search the user's uploaded financial documents (bank statements, "
            "expense data, loan documents) for relevant information. "
            "Use this to find specific transactions, spending patterns, "
            "income details, loan info, or any data from uploaded files. "
            "Input should be a natural language query describing what you're looking for."
        ),
        func=_rag_search,
    )

    tools = [rag_tool, tavily_tool]

    # ── ReAct sub-agents (one per specialist) ──────
    debt_react = create_react_agent(llm, tools)
    savings_react = create_react_agent(llm, tools)
    budget_react = create_react_agent(llm, tools)
    action_react = create_react_agent(llm, tools)

    # ── Node: Orchestrator ─────────────────────────
    def orchestrator_node(state: FinanceDoctorState) -> dict[str, Any]:
        """Classify query and set route_decision."""
        user_messages = [m for m in state["messages"] if isinstance(m, HumanMessage)]
        latest_query = user_messages[-1].content if user_messages else ""

        response = llm.invoke([
            SystemMessage(content=ORCHESTRATOR_SYSTEM_PROMPT),
            HumanMessage(content=latest_query),
        ])

        decision = response.content.strip().lower()

        # Normalise to valid route names
        if "debt" in decision:
            decision = "debt_analyzer"
        elif "saving" in decision or "invest" in decision:
            decision = "savings_strategy"
        elif "action" in decision or "plan" in decision or "step" in decision or "priorit" in decision:
            decision = "action_planner"
        else:
            decision = "budget_advisor"

        return {"route_decision": decision}

    # ── Node runners (generic, parameterised) ──────
    def _run_specialist(state: FinanceDoctorState, agent, system_prompt_template: str) -> dict[str, Any]:
        """Run a specialist ReAct agent."""
        data_block = _build_data_block(state)
        system = system_prompt_template.replace("{financial_data_block}", data_block)

        input_messages = [SystemMessage(content=system)] + state["messages"]
        result = agent.invoke({"messages": input_messages})

        # Extract the final AI message
        ai_msgs = [
            m for m in result["messages"]
            if isinstance(m, AIMessage) and m.content and not m.tool_calls
        ]
        final = ai_msgs[-1] if ai_msgs else AIMessage(content="I could not generate a response. Please try rephrasing your question.")
        return {"messages": [final]}

    # ── Specialist nodes ───────────────────────────
    def debt_node(state: FinanceDoctorState) -> dict[str, Any]:
        return _run_specialist(state, debt_react, DEBT_AGENT_SYSTEM_PROMPT)

    def savings_node(state: FinanceDoctorState) -> dict[str, Any]:
        return _run_specialist(state, savings_react, SAVINGS_AGENT_SYSTEM_PROMPT)

    def budget_node(state: FinanceDoctorState) -> dict[str, Any]:
        return _run_specialist(state, budget_react, BUDGET_AGENT_SYSTEM_PROMPT)

    def action_node(state: FinanceDoctorState) -> dict[str, Any]:
        return _run_specialist(state, action_react, ACTION_AGENT_SYSTEM_PROMPT)

    # ── Conditional routing edge ───────────────────
    def route_fn(state: FinanceDoctorState) -> str:
        return state.get("route_decision", "budget_advisor")

    # ── Build the graph ────────────────────────────
    graph = StateGraph(FinanceDoctorState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("debt_analyzer", debt_node)
    graph.add_node("savings_strategy", savings_node)
    graph.add_node("budget_advisor", budget_node)
    graph.add_node("action_planner", action_node)

    graph.add_edge(START, "orchestrator")
    graph.add_conditional_edges(
        "orchestrator",
        route_fn,
        {
            "debt_analyzer": "debt_analyzer",
            "savings_strategy": "savings_strategy",
            "budget_advisor": "budget_advisor",
            "action_planner": "action_planner",
        },
    )
    graph.add_edge("debt_analyzer", END)
    graph.add_edge("savings_strategy", END)
    graph.add_edge("budget_advisor", END)
    graph.add_edge("action_planner", END)

    return graph.compile()
