"""
agents/planner.py — Query Planner + Dynamic Tool Router

THE TRIAGE NURSE of the system.

This agent does TWO jobs:
  1. Decompose: Break the user query into 2-4 focused sub-queries
  2. Route: For each sub-query, decide WHICH tools the Retriever should use

The routing decision is baked into the output JSON — the Retriever reads this
and executes accordingly. No if-else logic. No hardcoded rules.
The LLM makes the call based on the tool descriptions in its system prompt.

Routing logic (learned by LLM from prompt context):
  - Sports / News / Pop Culture / Current Events → tavily_web_search ONLY
  - Physics / CS / Math / Science / Academic     → arxiv_search + maybe tavily_web_search
  - Content from user docs                       → chroma_local (always optional companion)
  - General knowledge                            → tavily_web_search (default)

Output contract: Valid JSON list of SubQueryRoute objects. Nothing else.
"""

import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from core.state import ResearchState, SubQueryRoute


PLANNER_SYSTEM_PROMPT = """You are an expert Research Strategist and Query Router. You have two responsibilities:

## Responsibility 1: Query Decomposition
Break the user's research question into 2-4 focused, self-contained sub-queries that together provide comprehensive coverage of the topic.

## Responsibility 2: Tool Routing
For each sub-query, decide which retrieval tools to use. You have exactly THREE tools available to the retrieval team:

**Tool 1: tavily_web_search**
- USE FOR: Current events, sports statistics, celebrity/pop culture, news, company updates, product releases, stock prices, real-time data, anything that changes day-to-day.
- DO NOT USE FOR: Academic theories or scientific papers (use arxiv_search instead).
- Example triggers: "latest", "current", "today", "2024 stats", "recent news", names of athletes/celebrities, company earnings.

**Tool 2: arxiv_search**
- USE FOR: Scientific theories, academic research papers, peer-reviewed studies, physics, mathematics, computer science, AI/ML, biology, economics research.
- DO NOT USE FOR: Current events, sports, celebrity info, or anything not academic.
- Example triggers: "theory of", "research on", "papers about", "mechanism of", scientific terminology like "Hawking radiation", "transformer architecture", "CRISPR", "quantum entanglement".

**Tool 3: chroma_local**
- USE FOR: Content from user-uploaded PDF documents. Add this as a supplementary tool whenever the topic might be covered in uploaded research papers.
- Always include this as a companion tool for academic queries in case the user has uploaded relevant PDFs.

## Routing Decision Matrix (internalize this):
| Query Type | Tools to Use |
|---|---|
| Sports / Celebrity / News | [tavily_web_search] |
| Academic / Scientific | [arxiv_search, chroma_local] |
| Academic + Breaking Developments | [arxiv_search, tavily_web_search, chroma_local] |
| General Knowledge | [tavily_web_search] |
| Technology / AI / CS | [arxiv_search, tavily_web_search, chroma_local] |

## Output Format
You MUST output ONLY a valid JSON array. No markdown. No explanation. No preamble.
Each element must have exactly these fields:
- "sub_query": string (the focused sub-question)
- "tools": array of strings from ["tavily_web_search", "arxiv_search", "chroma_local"]
- "rationale": string (1 sentence explaining why these tools were chosen)

## Example Output:
[
  {
    "sub_query": "Virat Kohli batting average and recent IPL 2024 performance",
    "tools": ["tavily_web_search"],
    "rationale": "Real-time sports statistics require live web search; academic databases have no cricket data."
  },
  {
    "sub_query": "Hawking radiation theoretical framework and information paradox",
    "tools": ["arxiv_search", "chroma_local"],
    "rationale": "Academic physics topic best covered by peer-reviewed papers and any uploaded astrophysics PDFs."
  }
]"""


def planner_node(state: ResearchState, llm: ChatOpenAI) -> ResearchState:
    """
    Triage nurse node: decomposes query AND assigns tool routes per sub-query.

    Args:
        state: Current ResearchState
        llm  : Initialized ChatOpenAI instance

    Returns:
        Updated state with sub_queries and routing_plan populated
    """
    print(f"[Planner] Decomposing and routing: '{state['user_query']}'")

    user_prompt = f"""Decompose this research question and route each sub-query to the appropriate tools:

Research Question: {state['user_query']}

Remember: Output ONLY a valid JSON array. Nothing else."""

    try:
        response = llm.invoke([
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])

        raw_output = response.content.strip()

        # Strip markdown code fences if the LLM added them despite instructions
        if raw_output.startswith("```"):
            raw_output = raw_output.strip("`").strip()
            if raw_output.startswith("json"):
                raw_output = raw_output[4:].strip()

        routing_plan: list[SubQueryRoute] = json.loads(raw_output)

        # Validate structure
        if not isinstance(routing_plan, list) or not routing_plan:
            raise ValueError("Planner returned empty or non-list output.")

        for item in routing_plan:
            if "sub_query" not in item or "tools" not in item:
                raise ValueError(f"Malformed routing plan item: {item}")

        # Cap at 4 sub-queries to control costs
        routing_plan = routing_plan[:4]
        sub_queries = [item["sub_query"] for item in routing_plan]

        print(f"[Planner] Generated {len(routing_plan)} routed sub-queries:")
        for item in routing_plan:
            print(f"  → '{item['sub_query']}' | Tools: {item['tools']}")

        return {
            **state,
            "sub_queries": sub_queries,
            "routing_plan": routing_plan,
            "current_agent": "Query Planner + Router ✅",
        }

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        # Fallback: treat full query as one sub-query, use all tools
        print(f"[Planner] Parse failed ({e}), falling back to full query with all tools.")
        fallback_plan: list[SubQueryRoute] = [{
            "sub_query": state["user_query"],
            "tools": ["tavily_web_search", "arxiv_search", "chroma_local"],
            "rationale": "Fallback routing — using all tools due to planning error.",
        }]
        return {
            **state,
            "sub_queries": [state["user_query"]],
            "routing_plan": fallback_plan,
            "current_agent": "Query Planner + Router ⚠️ (fallback)",
        }