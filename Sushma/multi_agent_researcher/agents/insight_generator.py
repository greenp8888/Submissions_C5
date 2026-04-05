"""Insight Generation Agent — produces hypotheses and trend analysis.

Receives the analysis summary and contradictions from the Analyzer,
then generates novel insights using explicit chain-of-thought reasoning.
Produces hypotheses, emerging trends, knowledge gaps, and future directions.
"""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from multi_agent_researcher.models.state import ResearchState

logger = logging.getLogger(__name__)

INSIGHT_GENERATOR_SYSTEM_PROMPT = """You are the Insight Generation Agent in a multi-agent research system.

You receive a synthesized analysis of research evidence and must generate
novel, well-reasoned insights. You do NOT just summarize — you reason forward.

## Your Task: Generate 3-5 Original Insights

Each insight must follow this reasoning chain format:
"Evidence [A] combined with [B] suggests [hypothesis/trend] because [reasoning]."

## Types of Insights to Generate (pick the most relevant)
1. **Emerging Trends**: Patterns forming across the evidence
2. **Hypotheses**: Testable predictions supported by the evidence
3. **Knowledge Gaps**: What is missing or under-researched
4. **Contradictions Resolved**: Your interpretation of conflicting claims
5. **Future Directions**: What research or actions the evidence points toward
6. **Practical Implications**: Real-world applications of the findings

## Output Format (MUST be valid JSON)
{
  "insights": [
    {
      "type": "emerging_trend | hypothesis | knowledge_gap | future_direction | practical_implication",
      "title": "Short descriptive title",
      "reasoning_chain": "Evidence X + Evidence Y suggests Z because...",
      "confidence": "high | medium | low",
      "implications": "What this means in practice"
    }
  ],
  "overall_assessment": "2-3 sentence synthesis of what the evidence collectively points toward",
  "recommended_next_steps": ["step 1", "step 2", "step 3"]
}

Output ONLY valid JSON. Use rigorous chain-of-thought reasoning, not speculation.
"""


def insight_generator_node(state: ResearchState, llm: ChatOpenAI) -> dict:
    """Insight Generator node — generates hypotheses and trend analysis.

    Args:
        state: The current ResearchState with analysis_summary populated.
        llm: The configured ChatOpenAI (OpenRouter) model.

    Returns:
        dict: State updates with insights list and status.
    """
    query = state["query"]
    summary = state.get("analysis_summary", "No analysis available.")
    contradictions = state.get("contradictions", [])
    validated_sources = state.get("validated_sources", [])

    logger.info("Insight Generator: generating insights for query='%s'", query[:60])
    print(f"\n{'='*60}")
    print(f"  AGENT: Insight Generator")
    print(f"{'='*60}")
    print(f"  Generating insights from analysis...")

    contradictions_block = ""
    if contradictions:
        contradictions_block = "\n\nIdentified Contradictions:\n" + "\n".join(
            f"- {c}" for c in contradictions
        )

    user_content = (
        f"Research Question: {query}\n\n"
        f"Analysis Summary:\n{summary}"
        f"{contradictions_block}\n\n"
        f"Validated Sources: {len(validated_sources)} sources confirmed credible.\n\n"
        f"Generate 3-5 original insights using explicit chain-of-thought reasoning."
    )

    messages = [
        SystemMessage(content=INSIGHT_GENERATOR_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]

    response = None
    try:
        response = llm.invoke(messages)
        raw = response.content.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        insight_data = json.loads(raw)
        raw_insights = insight_data.get("insights", [])
        overall = insight_data.get("overall_assessment", "")
        next_steps = insight_data.get("recommended_next_steps", [])

        # Flatten insights into readable strings for the state
        insights_list = []
        for ins in raw_insights:
            title = ins.get("title", "Insight")
            reasoning = ins.get("reasoning_chain", "")
            confidence = ins.get("confidence", "medium")
            implications = ins.get("implications", "")
            insight_type = ins.get("type", "general")

            formatted = (
                f"[{insight_type.upper()} | confidence={confidence}] "
                f"{title}: {reasoning}"
            )
            if implications:
                formatted += f" | Implications: {implications}"
            insights_list.append(formatted)

        if overall:
            insights_list.append(f"[OVERALL ASSESSMENT] {overall}")
        if next_steps:
            steps_str = " | ".join(next_steps)
            insights_list.append(f"[NEXT STEPS] {steps_str}")

    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("Insight Generator JSON parse failed (%s) — using fallback", exc)
        try:
            insights_list = [response.content] if response is not None else ["Insights could not be generated."]
        except Exception:
            insights_list = ["Insights could not be generated."]

    logger.info("Insight Generator complete: %d insights", len(insights_list))
    print(f"  Insights generated: {len(insights_list)}")

    return {
        "insights": insights_list,
        "status": f"insights_generated ({len(insights_list)} insights)",
        "messages": [HumanMessage(content=user_content)] + ([response] if response is not None else []),
    }
