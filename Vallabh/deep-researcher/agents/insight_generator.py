"""
=============================================================================
Insight Generation Agent
=============================================================================
Identifies emerging trends, generates hypotheses, builds reasoning chains,
and suggests future research directions based on all accumulated evidence.
=============================================================================
"""
from __future__ import annotations

import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from state import ResearchState, InsightResult
from config import settings

logger = logging.getLogger(__name__)

INSIGHT_SYSTEM_PROMPT = """You are a brilliant research synthesizer. Your job is to
go BEYOND summarizing what the sources say and generate original insights.

## Your Tasks:

### 1. Trend Identification
Find patterns across sources that point to emerging trends:
- What direction is the field moving?
- What technologies/approaches are gaining traction?
- What is declining or being replaced?
- Assign confidence: HIGH (strong multi-source evidence), MEDIUM (suggestive), LOW (speculative)

### 2. Hypothesis Generation
Based on the evidence, propose 2-4 novel hypotheses:
- Each must have a clear reasoning chain (step-by-step logic)
- Cite specific evidence from sources
- Note counter-evidence that could weaken the hypothesis
- Explain how the hypothesis could be tested
- Highlight what makes it novel (not just restating what sources say)

### 3. Future Research Directions
Suggest 3-5 specific research questions worth investigating next.
These should emerge from gaps, contradictions, or trends you identified.

### 4. Key Takeaways
Distill the top 3-5 most important takeaways for someone who just
wants the bottom line.

### 5. Synthesis Narrative
Write a connecting narrative (2-3 paragraphs) that weaves together
the trends, hypotheses, and takeaways into a coherent story.

## Important:
- Be intellectually bold but transparent about uncertainty
- Reasoning chains should be explicit: "Because A [source-id], and B [source-id], therefore C"
- Distinguish between what the evidence SHOWS vs. what you INFER
- Avoid generic insights — make them specific to the query topic
"""

INSIGHT_HUMAN_PROMPT = """## Original Research Query:
{query}

## Consensus Findings:
{consensus_text}

## Source Summaries:
{summaries_text}

## Contradictions:
{contradictions_text}

## Fact Check Results:
{factcheck_text}

## Overall Reliability: {reliability:.0%}

Generate deep insights, trends, and hypotheses from this research corpus.
"""


def generate_insights(state: ResearchState) -> dict:
    """
    Insight Generation Agent node for LangGraph.

    Reads: query, consensus_findings, source_summaries, contradictions,
           fact_checks, overall_reliability
    Writes: trends, hypotheses, future_directions, key_takeaways,
            synthesis_narrative, current_agent
    """
    logger.info("💡 Insight Generation Agent starting...")

    try:
        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.4,  # Slightly creative for hypothesis generation
            api_key=settings.OPENAI_API_KEY,
        ).with_structured_output(InsightResult)

        prompt = ChatPromptTemplate.from_messages([
            ("system", INSIGHT_SYSTEM_PROMPT),
            ("human", INSIGHT_HUMAN_PROMPT),
        ])
        chain = prompt | llm

        # Format inputs
        consensus_text = "\n".join(f"- {c}" for c in state.get("consensus_findings", [])) or "None found"
        summaries_text = "\n".join(
            f"[{s.get('source_id', '?')}] {', '.join(s.get('key_findings', [])[:3])}"
            for s in state.get("source_summaries", [])
        ) or "None"
        contradictions_text = "\n".join(
            f"- {c.get('claim', '?')}: {c.get('source_a_position', '')} vs {c.get('source_b_position', '')}"
            for c in state.get("contradictions", [])
        ) or "None"
        factcheck_text = "\n".join(
            f"- [{fc.get('status', '?')}] {fc.get('claim', '?')} (confidence: {fc.get('confidence', 0):.0%})"
            for fc in state.get("fact_checks", [])
        ) or "None"

        result: InsightResult = chain.invoke({
            "query": state["query"],
            "consensus_text": consensus_text,
            "summaries_text": summaries_text,
            "contradictions_text": contradictions_text,
            "factcheck_text": factcheck_text,
            "reliability": state.get("overall_reliability", 0.0),
        })

        logger.info(
            f"✅ Insights generated: {len(result.trends)} trends, "
            f"{len(result.hypotheses)} hypotheses, "
            f"{len(result.future_research_directions)} future directions"
        )

        return {
            "trends": [t.model_dump() for t in result.trends],
            "hypotheses": [h.model_dump() for h in result.hypotheses],
            "future_directions": result.future_research_directions,
            "key_takeaways": result.key_takeaways,
            "synthesis_narrative": result.synthesis_narrative,
            "current_agent": "insight_generator",
        }

    except Exception as e:
        logger.error(f"❌ Insight Generator failed: {e}")
        return {
            "trends": [],
            "hypotheses": [],
            "future_directions": [],
            "key_takeaways": ["Insight generation failed — see raw findings above"],
            "synthesis_narrative": f"Error: {str(e)}",
            "current_agent": "insight_generator",
            "error_trace": [f"Insight Generator Error: {str(e)}"],
        }
