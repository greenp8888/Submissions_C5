"""
=============================================================================
Fact Checker Agent
=============================================================================
Cross-validates key claims identified in the analysis against all sources.
Assigns confidence scores and flags unsupported or contradicted claims.
=============================================================================
"""
from __future__ import annotations

import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from state import ResearchState, FactCheckResult
from config import settings

logger = logging.getLogger(__name__)

FACTCHECK_SYSTEM_PROMPT = """You are a rigorous fact-checker. Your job is to verify
key claims from a research analysis against the available source material.

## Instructions:
1. Extract the 5-10 most important factual claims from the consensus findings
   and source summaries.
2. For each claim, check it against ALL available sources:
   - VERIFIED: 2+ independent sources confirm it
   - PARTIALLY_VERIFIED: 1 credible source confirms, no contradictions
   - UNVERIFIED: No source directly confirms this claim
   - CONTRADICTED: At least one source directly contradicts this claim
3. Assign a confidence score (0.0 to 1.0):
   - 0.9-1.0: Multiple independent, high-credibility sources agree
   - 0.7-0.9: One high-credibility source, no contradictions
   - 0.5-0.7: Sources partially support, some ambiguity
   - 0.3-0.5: Weak support, possible contradictions
   - Below 0.3: Contradicted or unsupported
4. Note which specific sources support or contradict each claim.
5. Calculate overall reliability as the weighted average of claim confidences.

## Important:
- A claim can be true even if only one source mentions it (but confidence is lower)
- Wikipedia confirming something is weaker than a peer-reviewed paper confirming it
- Recency matters: an older source may be outdated on current facts
- Be precise about what exactly is verified vs. what is extrapolated
"""

FACTCHECK_HUMAN_PROMPT = """## Consensus Findings to Verify:
{consensus_text}

## Source Summaries:
{summaries_text}

## Contradictions Already Identified:
{contradictions_text}

## Full Source Content:
{sources_text}

Verify the key claims against all available evidence.
"""


def check_facts(state: ResearchState) -> dict:
    """
    Fact Checker Agent node for LangGraph.

    Reads: consensus_findings, source_summaries, contradictions, sources
    Writes: fact_checks, overall_reliability, reliability_summary, current_agent
    """
    logger.info("✅ Fact Checker Agent starting...")

    consensus = state.get("consensus_findings", [])
    summaries = state.get("source_summaries", [])
    sources = state.get("sources", [])

    if not consensus and not summaries:
        return {
            "fact_checks": [],
            "overall_reliability": 0.0,
            "reliability_summary": "No findings to fact-check.",
            "current_agent": "fact_checker",
        }

    try:
        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
        ).with_structured_output(FactCheckResult)

        prompt = ChatPromptTemplate.from_messages([
            ("system", FACTCHECK_SYSTEM_PROMPT),
            ("human", FACTCHECK_HUMAN_PROMPT),
        ])
        chain = prompt | llm

        # Format inputs
        consensus_text = "\n".join(f"- {c}" for c in consensus) or "None"
        summaries_text = "\n".join(
            f"[{s.get('source_id', '?')}] Findings: {', '.join(s.get('key_findings', [])[:3])}"
            for s in summaries
        ) or "None"
        contradictions_text = "\n".join(
            f"- {c.get('claim', '?')}: {c.get('source_a_id', '?')} vs {c.get('source_b_id', '?')}"
            for c in state.get("contradictions", [])
        ) or "None"
        sources_text = "\n".join(
            f"[{s.get('id', '?')}] {s.get('title', '?')}: {s.get('content', '')[:500]}"
            for s in sources[:15]  # Limit to avoid context overflow
        ) or "None"

        result: FactCheckResult = chain.invoke({
            "consensus_text": consensus_text,
            "summaries_text": summaries_text,
            "contradictions_text": contradictions_text,
            "sources_text": sources_text,
        })

        logger.info(
            f"✅ Fact checking complete: {len(result.checks)} claims verified, "
            f"reliability: {result.overall_reliability:.0%}"
        )

        return {
            "fact_checks": [fc.model_dump() for fc in result.checks],
            "overall_reliability": result.overall_reliability,
            "reliability_summary": result.reliability_summary,
            "current_agent": "fact_checker",
        }

    except Exception as e:
        logger.error(f"❌ Fact Checker failed: {e}")
        return {
            "fact_checks": [],
            "overall_reliability": 0.0,
            "reliability_summary": f"Fact checking failed: {str(e)}",
            "current_agent": "fact_checker",
            "error_trace": [f"Fact Checker Error: {str(e)}"],
        }
