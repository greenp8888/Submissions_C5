"""Query Planner Agent — decomposes research queries into sub-questions.

The entry node of the research pipeline. It receives the user's raw
research question, classifies the research type, generates 3-5 targeted
sub-queries, and selects which retrieval sources to use.
"""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from multi_agent_researcher.models.state import ResearchState

logger = logging.getLogger(__name__)

QUERY_PLANNER_SYSTEM_PROMPT = """You are the Query Planner Agent in a multi-agent research system.

Your job is to decompose the user's research question into targeted sub-queries
and select the most appropriate retrieval sources.

## Available Sources
- **arxiv**: Academic/scientific papers. Use for technical, scientific, and research topics.
- **tavily**: Real-time web search. Use for current events, recent developments, and industry news.
- **wikipedia**: Background knowledge. Use for foundational concepts, definitions, history.
- **serpapi**: Broad Google search. Use for general web sources, news, company info.
- **pdf**: User-provided documents. Include only if pdf_paths are specified in the task.

## Your Output Format (MUST be valid JSON)
Return ONLY a JSON object with this exact structure:
{
  "sub_queries": [
    "specific question 1",
    "specific question 2",
    "specific question 3",
    "specific question 4 (optional)",
    "specific question 5 (optional)"
  ],
  "sources_to_use": ["arxiv", "tavily", "wikipedia"],
  "research_type": "academic | current_events | technical | general",
  "reasoning": "brief explanation of your source selection"
}

## Rules
- Generate 3-5 sub-queries, each targeting a specific aspect of the main question.
- Sub-queries must be concrete and retrieval-ready (not vague or generic).
- Select 2-4 sources — do NOT use all sources unless the topic genuinely spans all of them.
- Academic topics → always include arxiv.
- Current events (2024-2026) → always include tavily.
- Foundational concepts → always include wikipedia.
- Output ONLY valid JSON. No markdown, no explanation outside the JSON.
"""


def query_planner_node(state: ResearchState, llm: ChatOpenAI) -> dict:
    """Query Planner node — decomposes the user query into sub-questions.

    Args:
        state: The current ResearchState.
        llm: The configured ChatOpenAI (OpenRouter) model.

    Returns:
        dict: State updates with sub_queries, sources_to_use, status,
              and appended messages.
    """
    query = state["query"]
    pdf_paths = state.get("pdf_paths", [])

    logger.info("Query Planner: decomposing query='%s'", query)
    print(f"\n{'='*60}")
    print(f"  AGENT: Query Planner")
    print(f"{'='*60}")
    print(f"  Decomposing: {query[:80]}...")

    user_content = f"Research Question: {query}"
    if pdf_paths:
        user_content += f"\n\nUser has provided {len(pdf_paths)} PDF document(s). Include 'pdf' in sources_to_use."

    messages = [
        SystemMessage(content=QUERY_PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]

    response = None
    try:
        response = llm.invoke(messages)
        raw = response.content.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        plan = json.loads(raw)
        sub_queries = plan.get("sub_queries", [query])
        sources = plan.get("sources_to_use", ["tavily", "wikipedia"])
        research_type = plan.get("research_type", "general")
        reasoning = plan.get("reasoning", "")

        # If user provided PDFs, ensure pdf source is included
        if pdf_paths and "pdf" not in sources:
            sources.append("pdf")

    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("Query Planner JSON parse failed (%s) — using defaults", exc)
        sub_queries = [query]
        sources = ["tavily", "wikipedia"]
        research_type = "general"
        reasoning = "Fallback: JSON parse error"

    logger.info(
        "Query Planner complete: %d sub_queries, sources=%s", len(sub_queries), sources
    )
    print(f"  Sub-queries: {len(sub_queries)} generated")
    print(f"  Sources selected: {sources}")

    return {
        "sub_queries": sub_queries,
        "sources_to_use": sources,
        "status": f"planned ({research_type})",
        "retrieval_attempts": 0,
        "messages": [HumanMessage(content=user_content)] + ([response] if response is not None else []),
    }
