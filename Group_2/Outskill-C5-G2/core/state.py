"""
core/state.py — LangGraph Shared State Schema

The relay baton passed between all agents.
Every agent reads from this, writes to this, and returns the updated version.

New field: `routing_plan`
  The Planner now outputs not just sub_queries but also WHICH TOOLS to use
  for each sub-query. This is the triage nurse's chart.
"""

from typing import TypedDict, List, Dict, Optional, Annotated
import operator


class SubQueryRoute(TypedDict):
    """
    A single sub-query paired with its routing decision.
    
    Example:
        {
            "sub_query": "Virat Kohli IPL 2024 stats",
            "tools": ["tavily_web_search"],
            "rationale": "Real-time sports data — not in academic databases"
        }
    """
    sub_query: str
    tools: List[str]       # Values: "tavily_web_search", "arxiv_search", "chroma_local"
    rationale: str         # Why this routing decision was made (for transparency)


class ResearchState(TypedDict):
    """
    Central state object flowing through the entire LangGraph DAG.

    Fields:
        user_query      : Original user question (never mutated)
        sub_queries     : Plain list of sub-query strings (for backward compat)
        routing_plan    : Enriched plan — each sub-query + its tool routing decision
        raw_documents   : All retrieved docs (accumulates via operator.add)
        analyzed_facts  : Analyst's cleaned synthesis with contradiction flags
        insights        : CoT-driven hypotheses from Insight Generator
        final_report    : Final structured Markdown report
        current_agent   : Active node name (for UI progress tracking)
        error           : Optional error message
        api_keys        : Dict containing tool API keys (e.g., tavily)
    """
    user_query: str
    sub_queries: List[str]
    routing_plan: List[SubQueryRoute]            # NEW: triage nurse's routing chart
    raw_documents: Annotated[List[Dict[str, str]], operator.add]
    analyzed_facts: str
    insights: str
    final_report: str
    current_agent: str
    error: Optional[str]
    api_keys: Dict[str, str]