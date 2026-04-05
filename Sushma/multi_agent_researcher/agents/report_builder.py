"""Report Builder Agent — compiles the final structured research report.

The terminal node of the research pipeline. Receives the complete
ResearchState and compiles all findings, analysis, and insights into
a structured Markdown report ready for the user.
"""

import logging
from datetime import datetime, timezone

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from multi_agent_researcher.models.state import ResearchState

logger = logging.getLogger(__name__)

REPORT_BUILDER_SYSTEM_PROMPT = """You are the Report Builder Agent in a multi-agent research system.

You are the FINAL agent. Your job is to compile all research findings into a
polished, professional, and structured Markdown research report.

## Required Report Structure (use EXACTLY these headings)

## Deep Research Report

### Research Question
[Restate the original research question clearly]

### Executive Summary
[2-3 paragraph synthesis of the most important findings — what does the evidence say?]

### Methodology
[List all sources consulted and the retrieval approach used]

### Key Findings
[Present the main findings as numbered points with inline citations showing source URLs]

### Contradictions & Caveats
[List conflicting claims found across sources and note any important limitations]

### Insights & Hypotheses
[Present each insight with its reasoning chain — these are the forward-looking conclusions]

### Conclusion
[Wrap up with 2-3 sentences answering the research question based on the evidence]

### References
[List all validated source URLs]

## Rules
- Use proper Markdown formatting (##, ###, -, *, **bold**, etc.)
- Include at least one URL reference in the References section
- Be specific — cite sources by name/URL where possible
- The report must be comprehensive (minimum 600 words)
- Do NOT truncate findings — include all key data points
"""


def report_builder_node(state: ResearchState, llm: ChatOpenAI) -> dict:
    """Report Builder node — compiles the final research report.

    This is the terminal node. It collects all state fields and uses
    the LLM to synthesize them into a structured Markdown report.

    Args:
        state: The complete ResearchState with all prior agent outputs.
        llm: The configured ChatOpenAI (OpenRouter) model.

    Returns:
        dict: State update with final_report and status set to "complete".
    """
    query = state["query"]
    sub_queries = state.get("sub_queries", [])
    sources_used = state.get("sources_to_use", [])
    docs = state.get("retrieved_documents", [])
    summary = state.get("analysis_summary", "No analysis available.")
    contradictions = state.get("contradictions", [])
    validated_sources = state.get("validated_sources", [])
    insights = state.get("insights", [])
    attempts = state.get("retrieval_attempts", 1)

    logger.info("Report Builder: compiling final report for query='%s'", query[:60])
    print(f"\n{'='*60}")
    print(f"  AGENT: Report Builder")
    print(f"{'='*60}")
    print(f"  Compiling report from {len(docs)} documents, {len(insights)} insights...")

    # Build a rich context block for the LLM
    sources_block = ", ".join(sources_used) if sources_used else "web"
    sub_q_block = "\n".join(f"- {q}" for q in sub_queries)
    contradictions_block = (
        "\n".join(f"- {c}" for c in contradictions)
        if contradictions
        else "No significant contradictions identified."
    )
    insights_block = "\n".join(f"- {ins}" for ins in insights) if insights else "No insights generated."
    validated_block = "\n".join(f"- {url}" for url in validated_sources[:15]) if validated_sources else "Sources not individually validated."

    # Collect all unique URLs from retrieved documents
    all_urls = list(
        {
            doc.get("url") or doc.get("pdf_url") or doc.get("file_path", "")
            for doc in docs
            if doc.get("url") or doc.get("pdf_url") or doc.get("file_path")
        }
    )[:20]
    all_urls_block = "\n".join(f"- {u}" for u in all_urls) if all_urls else "No URLs captured."

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    user_content = f"""Compile the final research report using ALL of the information below.

ORIGINAL QUESTION: {query}

SUB-QUESTIONS INVESTIGATED:
{sub_q_block}

SOURCES USED: {sources_block}
TOTAL DOCUMENTS RETRIEVED: {len(docs)} (across {attempts} retrieval round(s))
TIMESTAMP: {timestamp}

ANALYSIS SUMMARY:
{summary}

CONTRADICTIONS IDENTIFIED:
{contradictions_block}

INSIGHTS GENERATED:
{insights_block}

VALIDATED SOURCE URLS:
{validated_block}

ALL RETRIEVED URLs:
{all_urls_block}

Now write the complete, professional research report following the exact structure in your instructions.
"""

    messages = [
        SystemMessage(content=REPORT_BUILDER_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]

    response = None
    try:
        response = llm.invoke(messages)
        final_report = response.content.strip()
    except Exception as exc:
        logger.error("Report Builder LLM call failed: %s", exc)
        final_report = _build_fallback_report(state, timestamp)

    logger.info(
        "Report Builder complete: report_length=%d chars", len(final_report)
    )
    print(f"  Report compiled: {len(final_report)} characters")

    return {
        "final_report": final_report,
        "status": "complete",
        "messages": [HumanMessage(content=user_content)] + ([response] if response is not None else []),
    }


def _build_fallback_report(state: ResearchState, timestamp: str) -> str:
    """Build a minimal fallback report when LLM call fails.

    Args:
        state: The current ResearchState.
        timestamp: ISO timestamp string.

    Returns:
        str: A basic structured Markdown report.
    """
    query = state["query"]
    docs = state.get("retrieved_documents", [])
    insights = state.get("insights", [])
    summary = state.get("analysis_summary", "No analysis completed.")
    validated = state.get("validated_sources", [])

    urls = "\n".join(
        f"- {doc.get('url', '')}"
        for doc in docs[:10]
        if doc.get("url")
    )
    insights_str = "\n".join(f"- {i}" for i in insights)

    return f"""## Deep Research Report

### Research Question
{query}

### Executive Summary
{summary}

### Methodology
Sources consulted: {", ".join(state.get("sources_to_use", []))}
Documents retrieved: {len(docs)}
Generated: {timestamp}

### Key Findings
Analysis summary above represents synthesized findings from {len(docs)} retrieved documents.

### Contradictions & Caveats
{chr(10).join(f"- {c}" for c in state.get("contradictions", [])) or "None identified."}

### Insights & Hypotheses
{insights_str or "None generated."}

### Conclusion
Research completed. See executive summary for key findings.

### References
{urls or "No URLs captured."}
"""
