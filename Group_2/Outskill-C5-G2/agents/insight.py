"""
agents/insight.py — Insight Generator Node

The visionary. Takes validated facts and applies Chain-of-Thought
reasoning to surface non-obvious insights and testable hypotheses.

Analogy: The senior strategy partner who walks into a room full of
analysts' spreadsheets and says "Here's what this ACTUALLY means."
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from core.state import ResearchState


INSIGHT_SYSTEM_PROMPT = """You are a Senior Research Scientist with 20+ years of cross-disciplinary expertise. You specialize in connecting disparate findings into coherent, actionable narratives.

Apply EXPLICIT Chain-of-Thought reasoning. Show your thinking step by step.

Structure your output with these exact headers:

## Chain-of-Thought Reasoning
Show your thinking process explicitly. Connect data points. Build toward conclusions step by step. Example format:
"Observation 1: [fact]. Observation 2: [fact]. If [O1] and [O2] are both true, then [logical consequence]. This suggests [hypothesis]."

## Key Insights
3-5 non-obvious insights. Each insight MUST:
- Connect at least 2 data points from the validated facts
- Go beyond restating the facts (what does it MEAN?)
- Include confidence level: [HIGH/MEDIUM/LOW] with justification

## Hypotheses
2-3 testable hypotheses that emerge from the data. Clearly label these as UNCONFIRMED HYPOTHESES.
Format: "Hypothesis: [statement]. Evidence for: [X]. Evidence against: [Y]. How to test: [Z]."

## Strategic Implications
What do these insights mean for practitioners, researchers, or decision-makers? Who should care and why?

## Open Questions
What would a thoughtful senior researcher want to investigate next?

Rules:
- NEVER present a hypothesis as a confirmed fact
- If the data is insufficient for strong insights, say so explicitly
- Intellectual honesty > impressive-sounding conclusions"""


def insight_node(state: ResearchState, llm: ChatOpenAI) -> ResearchState:
    """
    Insight Generator node: CoT reasoning over validated facts.

    Args:
        state: ResearchState with analyzed_facts populated
        llm  : Initialized LLM

    Returns:
        Updated state with insights populated
    """
    print("[Insight Generator] Generating insights via Chain-of-Thought...")

    user_prompt = f"""Original Research Question: {state['user_query']}

Validated Facts from Critical Analysis:
{state['analyzed_facts']}

Apply Chain-of-Thought reasoning to generate deep insights and hypotheses."""

    try:
        response = llm.invoke([
            SystemMessage(content=INSIGHT_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])

        print(f"[Insight Generator] Insights generated ({len(response.content)} chars).")
        return {
            **state,
            "insights": response.content,
            "current_agent": "Insight Generator ✅",
        }

    except Exception as e:
        error_msg = f"Insight node failed: {str(e)}"
        print(f"[Insight Generator] ERROR: {error_msg}")
        return {
            **state,
            "insights": f"Insight generation failed: {error_msg}",
            "current_agent": "Insight Generator ❌",
            "error": error_msg,
        }