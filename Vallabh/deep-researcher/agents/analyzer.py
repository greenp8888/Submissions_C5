"""
=============================================================================
Critical Analysis Agent
=============================================================================
Summarizes findings per source, highlights contradictions between sources,
validates source credibility, and identifies information gaps.

Key Pattern: Large context synthesis with structured output
=============================================================================
"""
from __future__ import annotations

import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from state import ResearchState, AnalysisResult
from config import settings

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM_PROMPT = """You are an expert research analyst performing critical analysis
on a corpus of sources gathered to answer a research question.

## Your Tasks:
1. **Source Summaries**: For each source, extract key findings and assess credibility.
   - Credibility levels: HIGH (peer-reviewed, established institution), MEDIUM (reputable
     news, well-cited report), LOW (blog, opinion, single author without credentials)
   - Note limitations of each source

2. **Contradictions**: Identify where sources disagree. For each contradiction:
   - State the claim in dispute
   - What each source says
   - Your assessment of which is more credible and why

3. **Information Gaps**: Identify what the sources DON'T cover that would be needed
   to fully answer the research query. Suggest specific queries to fill gaps.

4. **Consensus Findings**: List findings that are supported by multiple sources.
   These are the most reliable conclusions.

5. **Overall Assessment**: How well does this corpus answer the research question?
   What is the overall quality of the evidence?

## Important:
- Be skeptical but fair — not every disagreement is a contradiction
- Wikipedia is useful for context but should not be a primary source for cutting-edge claims
- Recency matters: newer sources may override older ones on fast-moving topics
- Note if sources are citing each other (not independent corroboration)
"""

ANALYSIS_HUMAN_PROMPT = """## Research Query:
{query}

## Sub-Questions Being Investigated:
{sub_questions_text}

## Retrieved Sources:
{sources_text}

Analyze these sources critically. Identify consensus, contradictions, gaps, and
assess each source's credibility.
"""


def _format_sources_for_prompt(sources: list[dict]) -> str:
    lines = []
    for s in sources:
        lines.append(
            f"[{s.get('id', '?')}] {s.get('source_type', '?')} — {s.get('title', 'Untitled')}\n"
            f"  URL: {s.get('url', 'N/A')}\n"
            f"  Authors: {s.get('authors', 'N/A')}\n"
            f"  Published: {s.get('published_date', 'N/A')}\n"
            f"  Content:\n  {s.get('content', 'No content')[:1500]}\n"
        )
    return "\n---\n".join(lines) or "No sources available."


def _format_sub_questions(sub_questions: list[dict]) -> str:
    return "\n".join(
        f"  Q{sq.get('id', '?')}: {sq.get('question', 'N/A')}"
        for sq in sub_questions
    ) or "None"


def analyze_sources(state: ResearchState) -> dict:
    """
    Critical Analysis Agent node for LangGraph.

    Reads: query, sub_questions, sources
    Writes: source_summaries, contradictions, information_gaps,
            consensus_findings, analysis_assessment, has_critical_gaps, current_agent
    """
    logger.info("🔬 Critical Analysis Agent starting...")

    sources = state.get("sources", [])
    if not sources:
        return {
            "source_summaries": [],
            "contradictions": [],
            "information_gaps": [],
            "consensus_findings": [],
            "analysis_assessment": "No sources to analyze.",
            "has_critical_gaps": True,
            "current_agent": "analyzer",
        }

    try:
        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY,
        ).with_structured_output(AnalysisResult)

        prompt = ChatPromptTemplate.from_messages([
            ("system", ANALYSIS_SYSTEM_PROMPT),
            ("human", ANALYSIS_HUMAN_PROMPT),
        ])
        chain = prompt | llm

        result: AnalysisResult = chain.invoke({
            "query": state["query"],
            "sub_questions_text": _format_sub_questions(state.get("sub_questions", [])),
            "sources_text": _format_sources_for_prompt(sources),
        })

        # Determine if there are critical gaps
        critical_gaps = any(
            "critical" in gap.description.lower() or "essential" in gap.description.lower()
            for gap in result.information_gaps
        )
        has_gaps = len(result.information_gaps) >= 3 or critical_gaps

        logger.info(
            f"✅ Analysis complete: {len(result.source_summaries)} summaries, "
            f"{len(result.contradictions)} contradictions, "
            f"{len(result.information_gaps)} gaps"
        )

        return {
            "source_summaries": [s.model_dump() for s in result.source_summaries],
            "contradictions": [c.model_dump() for c in result.contradictions],
            "information_gaps": [g.model_dump() for g in result.information_gaps],
            "consensus_findings": result.consensus_findings,
            "analysis_assessment": result.overall_assessment,
            "has_critical_gaps": has_gaps,
            "current_agent": "analyzer",
        }

    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        return {
            "source_summaries": [],
            "contradictions": [],
            "information_gaps": [],
            "consensus_findings": [],
            "analysis_assessment": f"Analysis failed: {str(e)}",
            "has_critical_gaps": False,
            "current_agent": "analyzer",
            "error_trace": [f"Analyzer Error: {str(e)}"],
        }
