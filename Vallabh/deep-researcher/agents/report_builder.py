"""
=============================================================================
Report Builder Agent
=============================================================================
Compiles all research findings into a structured report with:
- Executive summary, methodology, findings, conclusions
- Inline citations referencing source IDs
- Confidence assessment
- Limitations section
- Renders as Markdown for export
=============================================================================
"""
from __future__ import annotations

import logging
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from state import ResearchState, ResearchReport
from config import settings

logger = logging.getLogger(__name__)

REPORT_SYSTEM_PROMPT = """You are a professional research report writer. Compile
the research findings into a well-structured, publication-quality report.

## Report Structure:
1. **Title**: Descriptive, specific title for the research
2. **Executive Summary**: 3-5 sentences covering the key findings and conclusions
3. **Methodology**: Briefly describe the multi-agent research approach, sources used,
   and how findings were verified
4. **Findings Sections**: Create 3-6 logical sections covering different aspects of
   the research. Each section should:
   - Have a clear heading
   - Present findings with inline citations using [source-id] format
   - Distinguish between verified facts and interpretations
5. **Conclusions**: Synthesize the overall answer to the research question
6. **Limitations**: What this research could NOT answer or verify
7. **References**: List all source IDs with their titles

## Important:
- Cite sources inline as [source-id] (e.g., [arxiv-001], [web-003])
- Note the confidence level of key claims
- If sources contradict, present both sides fairly
- Use the fact-check results to inform confidence statements
- Include the key takeaways and trends from the insight analysis
- Write in clear, accessible language (avoid unnecessary jargon)
"""

REPORT_HUMAN_PROMPT = """## Research Query:
{query}

## Key Takeaways:
{takeaways_text}

## Synthesis Narrative:
{narrative}

## Trends:
{trends_text}

## Hypotheses:
{hypotheses_text}

## Consensus Findings:
{consensus_text}

## Contradictions:
{contradictions_text}

## Fact Check Summary:
Overall Reliability: {reliability:.0%}
{factcheck_text}

## Sources:
{sources_list}

## Information Gaps:
{gaps_text}

Compile this into a comprehensive research report with proper citations.
"""


def _format_sources_list(sources: list[dict]) -> str:
    return "\n".join(
        f"[{s.get('id', '?')}] {s.get('source_type', '?')} — {s.get('title', 'Untitled')} "
        f"({s.get('url', 'no URL')})"
        for s in sources
    ) or "No sources"


def build_report(state: ResearchState) -> dict:
    """
    Report Builder Agent node for LangGraph.

    Reads: All accumulated state
    Writes: report, report_markdown, current_agent
    """
    logger.info("📝 Report Builder Agent starting...")

    try:
        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.2,
            api_key=settings.OPENAI_API_KEY,
        ).with_structured_output(ResearchReport)

        prompt = ChatPromptTemplate.from_messages([
            ("system", REPORT_SYSTEM_PROMPT),
            ("human", REPORT_HUMAN_PROMPT),
        ])
        chain = prompt | llm

        # Format all inputs
        takeaways_text = "\n".join(f"- {t}" for t in state.get("key_takeaways", [])) or "None"
        narrative = state.get("synthesis_narrative", "No narrative generated")
        trends_text = "\n".join(
            f"- {t.get('title', '?')}: {t.get('description', '')[:200]}"
            for t in state.get("trends", [])
        ) or "None"
        hypotheses_text = "\n".join(
            f"- {h.get('statement', '?')} (Reasoning: {' -> '.join(h.get('reasoning_chain', [])[:3])})"
            for h in state.get("hypotheses", [])
        ) or "None"
        consensus_text = "\n".join(f"- {c}" for c in state.get("consensus_findings", [])) or "None"
        contradictions_text = "\n".join(
            f"- {c.get('claim', '?')}: {c.get('source_a_position', '')} vs {c.get('source_b_position', '')}"
            for c in state.get("contradictions", [])
        ) or "None"
        factcheck_text = "\n".join(
            f"- [{fc.get('status', '?')}] {fc.get('claim', '?')} ({fc.get('confidence', 0):.0%})"
            for fc in state.get("fact_checks", [])
        ) or "None"
        gaps_text = "\n".join(
            f"- {g.get('description', '?')}"
            for g in state.get("information_gaps", [])
        ) or "None"

        result: ResearchReport = chain.invoke({
            "query": state["query"],
            "takeaways_text": takeaways_text,
            "narrative": narrative,
            "trends_text": trends_text,
            "hypotheses_text": hypotheses_text,
            "consensus_text": consensus_text,
            "contradictions_text": contradictions_text,
            "reliability": state.get("overall_reliability", 0.0),
            "factcheck_text": factcheck_text,
            "sources_list": _format_sources_list(state.get("sources", [])),
            "gaps_text": gaps_text,
        })

        # Render as markdown
        markdown = _render_markdown(result)

        logger.info(f"✅ Report generated: {result.title}")

        return {
            "report": result.model_dump(),
            "report_markdown": markdown,
            "current_agent": "report_builder",
        }

    except Exception as e:
        logger.error(f"❌ Report Builder failed: {e}")
        return {
            "report": {},
            "report_markdown": f"# Report Generation Failed\n\nError: {str(e)}",
            "current_agent": "report_builder",
            "error_trace": [f"Report Builder Error: {str(e)}"],
        }


def _render_markdown(report: ResearchReport) -> str:
    """Convert ResearchReport to a formatted Markdown document."""
    lines = [
        f"# {report.title}",
        f"*Generated: {report.generated_at}*",
        "",
        "---",
        "",
        "## Executive Summary",
        report.executive_summary,
        "",
        "## Methodology",
        report.methodology,
        "",
    ]

    for section in report.sections:
        lines.append(f"## {section.heading}")
        lines.append(section.content)
        if section.citations:
            lines.append(f"\n*Sources: {', '.join(section.citations)}*")
        lines.append("")

    lines.extend([
        "## Conclusions",
        report.conclusions,
        "",
        "## Confidence Assessment",
        report.confidence_assessment,
        "",
        "## Limitations",
        report.limitations,
        "",
        "## References",
    ])

    for ref in report.references:
        lines.append(f"- {ref}")

    return "\n".join(lines)
