"""
=============================================================================
Query Planner Agent
=============================================================================
Decomposes a complex research query into structured sub-questions.
This enables targeted multi-source retrieval and ensures comprehensive coverage.

Key Pattern: LLM with Pydantic structured output (QueryPlan)
=============================================================================
"""
from __future__ import annotations

import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from state import ResearchState, QueryPlan
from config import settings

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are an expert research strategist. Your job is to decompose
a complex research query into a structured investigation plan.

## Instructions:
1. Analyze the query to understand its full scope.
2. Break it into 3-7 sub-questions that together cover all aspects of the query.
3. For each sub-question:
   - Write a clear, specific question
   - Explain why it matters for answering the main query
   - Suggest 2-4 search keywords (optimized for academic and web search)
   - Assign priority (1=highest, must answer; 5=nice to have)
4. Define the research scope — what IS and IS NOT included.
5. Suggest which source types would be most useful (academic papers, news, reports, etc.)

## Depth Guidance:
- "quick": 3-4 sub-questions, focus on key facts only
- "standard": 4-6 sub-questions, balanced depth
- "deep": 5-7 sub-questions, comprehensive coverage with edge cases

## Important:
- Sub-questions should be MECE (mutually exclusive, collectively exhaustive)
- Order by logical dependency (foundational questions first)
- Include at least one question about recent developments/current state
- Include at least one question about limitations or open problems
"""

PLANNER_HUMAN_PROMPT = """Research Query: {query}
Research Depth: {depth}

Decompose this into a structured research plan."""


def plan_query(state: ResearchState) -> dict:
    """
    Query Planner node for LangGraph.

    Reads: query, depth
    Writes: query_plan, sub_questions, current_agent
    """
    logger.info("📋 Query Planner starting...")

    query = state["query"]
    depth = state.get("depth", "standard")

    if not query or not query.strip():
        return {
            "query_plan": {},
            "sub_questions": [],
            "current_agent": "query_planner",
            "error_trace": ["Query Planner: Empty query received"],
        }

    try:
        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.3,
            api_key=settings.OPENAI_API_KEY,
        ).with_structured_output(QueryPlan)

        prompt = ChatPromptTemplate.from_messages([
            ("system", PLANNER_SYSTEM_PROMPT),
            ("human", PLANNER_HUMAN_PROMPT),
        ])
        chain = prompt | llm

        plan: QueryPlan = chain.invoke({"query": query, "depth": depth})

        # Sort sub-questions by priority
        sorted_subs = sorted(plan.sub_questions, key=lambda sq: sq.priority)

        logger.info(
            f"✅ Query decomposed into {len(sorted_subs)} sub-questions "
            f"(scope: {plan.research_scope[:80]}...)"
        )

        return {
            "query_plan": plan.model_dump(),
            "sub_questions": [sq.model_dump() for sq in sorted_subs],
            "current_agent": "query_planner",
        }

    except Exception as e:
        logger.error(f"❌ Query Planner failed: {e}")
        # Fallback: use the original query as-is
        fallback_sq = {
            "id": 1, "question": query, "reasoning": "Direct query (planner failed)",
            "search_keywords": query.split()[:5], "priority": 1,
        }
        return {
            "query_plan": {"original_query": query, "research_scope": "Fallback", "sub_questions": [fallback_sq]},
            "sub_questions": [fallback_sq],
            "current_agent": "query_planner",
            "error_trace": [f"Query Planner Error (using fallback): {str(e)}"],
        }
