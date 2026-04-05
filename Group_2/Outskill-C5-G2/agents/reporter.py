"""
agents/reporter.py — Report Builder Node

The editor. Takes all upstream agent outputs and packages them into
a polished, structured, cited Markdown report.

Analogy: The McKinsey senior partner who converts analysts' work
into a board-ready deck in under 30 minutes.

Changes from v1:
- Citations now preserve EXACT ArXiv paper URLs + titles (no more generic labels)
- Execution timer added — tracks time taken for this node specifically
- System prompt updated to enforce exact URL preservation in citations
"""

import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from core.state import ResearchState


REPORTER_SYSTEM_PROMPT = """You are a world-class research editor and technical writer. Compile a comprehensive, beautifully structured research report.

You MUST use EXACTLY these Markdown headers in this order — no additions, no omissions:

# [Descriptive Report Title Based on the Research Question]

## Executive Summary
2-3 paragraphs. Must be fully understandable without reading the full report. Include the most important finding in the first sentence.

## Key Findings
Bullet-point list. Each bullet = one distinct, validated finding. Include source attribution like [Web] or [ArXiv] or [Local Doc] to indicate provenance.

## Critical Analysis
Detailed section covering: what the evidence shows, contradictions between sources, and honest assessment of data quality. Do not sugarcoat weak evidence.

## Insights & Hypotheses
The forward-looking section. Present insights and hypotheses from the research. Clearly distinguish CONFIRMED FINDINGS from HYPOTHESES using bold labels.

## Limitations & Caveats
What this research could NOT determine. Gaps in available data. What requires further investigation to confirm.

## Citations
CRITICAL RULE: You MUST copy each citation EXACTLY as provided in the Source Citations block below.
Do NOT paraphrase, rename, shorten, or generalize any citation.
Do NOT write "ArXiv Quantum Physics Repository" if the input says "https://arxiv.org/abs/2401.12345".
Every citation must be a direct, copy-pasteable URL or exact source name as given.

Format each citation exactly as:
[N] <EXACT title if provided> — <EXACT URL or source name> — via <tool name>

Example of CORRECT citation:
[1] Attention Is All You Need — https://arxiv.org/abs/1706.03762 — via arxiv_search

Example of WRONG citation (DO NOT DO THIS):
[1] ArXiv Research Paper — via arxiv_search

Rules:
- Use inline citation markers [1], [2] etc. where relevant throughout the report body
- Bold key terms on first use
- Professional tone: think Nature journal meets McKinsey report
- Do NOT add any text outside the defined headers
- Every claim in Key Findings must have at least one inline citation"""


def _build_citations_block(raw_documents: list) -> tuple[str, dict]:
    """
    Build a rich, deduplicated citations block from raw retrieved documents.

    For ArXiv results: extracts paper title from content and pairs it with
    the exact paper URL (entry_id). This prevents the LLM from collapsing
    specific paper URLs into generic labels like "ArXiv Repository".

    For web results: uses exact URL as-is.
    For local ChromaDB results: uses filename as-is.

    Args:
        raw_documents: List of document dicts from retriever node

    Returns:
        Tuple of:
            - citations_text (str): Formatted citations block for the prompt
            - citation_map (dict): citation_num → source URL (for debugging)
    """
    citations_text = ""
    citation_map   = {}
    seen           = set()
    citation_num   = 1

    for doc in raw_documents:
        src      = doc.get("source", "Unknown")
        tool     = doc.get("tool_used", "unknown")
        content  = doc.get("content", "")

        # Skip error entries and duplicates
        if not src or "error" in src.lower() or src in seen:
            continue

        # ── ArXiv papers: extract title from content ──────────────────────
        # ArXiv tool returns content in format:
        #   "Title: Attention Is All You Need\nAuthors: ...\nAbstract: ..."
        # We extract the title to make citations human-readable AND keep the URL
        if "arxiv" in tool.lower() and "Title:" in content:
            lines = content.strip().split("\n")
            title = ""
            for line in lines:
                if line.startswith("Title:"):
                    title = line.replace("Title:", "").strip()
                    break

            if title and src.startswith("http"):
                # Full citation: Title + exact URL
                citation_entry = f"[{citation_num}] {title} — {src} — via {tool}\n"
            elif src.startswith("http"):
                # URL only (title extraction failed)
                citation_entry = f"[{citation_num}] {src} — via {tool}\n"
            else:
                citation_entry = f"[{citation_num}] {src} — via {tool}\n"

        # ── Web results (Tavily): use URL directly ─────────────────────────
        elif "tavily" in tool.lower():
            citation_entry = f"[{citation_num}] {src} — via {tool}\n"

        # ── Local ChromaDB: use filename ───────────────────────────────────
        elif "chroma" in tool.lower():
            citation_entry = f"[{citation_num}] Local document: {src} — via {tool}\n"

        # ── Fallback ───────────────────────────────────────────────────────
        else:
            citation_entry = f"[{citation_num}] {src} — via {tool}\n"

        citations_text += citation_entry
        citation_map[citation_num] = src
        seen.add(src)
        citation_num += 1

    return citations_text, citation_map


def report_builder_node(state: ResearchState, llm: ChatOpenAI) -> ResearchState:
    """
    Report Builder node: compiles all agent outputs into structured Markdown.

    Now includes:
    - Exact citation URL preservation (ArXiv paper titles + URLs)
    - Per-node execution timer (logged to console + stored in report footer)

    Args:
        state: ResearchState with analyzed_facts and insights populated
        llm  : Initialized LLM

    Returns:
        Updated state with final_report populated and timing metadata
    """
    node_start_time = time.time()  # ← Start timer for THIS node
    print("[Report Builder] Compiling final report...")

    # ── BUILD CITATIONS BLOCK ─────────────────────────────────────────────
    citations_text, citation_map = _build_citations_block(state["raw_documents"])

    print(f"[Report Builder] Built {len(citation_map)} unique citations.")
    if citation_map:
        for num, src in citation_map.items():
            print(f"  [{num}] {src[:80]}{'...' if len(src) > 80 else ''}")

    # ── BUILD USER PROMPT ─────────────────────────────────────────────────
    user_prompt = f"""Compile a comprehensive research report from the following inputs.

**Original Research Question:** {state['user_query']}

**Sub-Queries Investigated:**
{chr(10).join(f'- {q}' for q in state['sub_queries'])}

**Tool Routing Used:**
{chr(10).join(f"- '{r['sub_query']}' → {r['tools']}" for r in state.get('routing_plan', []))}

**Critical Analysis:**
{state['analyzed_facts']}

**Insights & Hypotheses:**
{state['insights']}

**Source Citations (COPY THESE EXACTLY — DO NOT PARAPHRASE OR RENAME):**
{citations_text if citations_text else 'No external sources retrieved.'}

REMINDER: Every citation above must appear in the ## Citations section EXACTLY as written.
Do not rename URLs. Do not replace paper titles with generic labels.

Generate the complete structured Markdown report now."""

    # ── LLM CALL ──────────────────────────────────────────────────────────
    try:
        llm_start = time.time()

        response = llm.invoke([
            SystemMessage(content=REPORTER_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])

        llm_elapsed    = time.time() - llm_start       # Time for just the LLM call
        node_elapsed   = time.time() - node_start_time  # Total time for this node

        print(f"[Report Builder] LLM call: {llm_elapsed:.2f}s | Node total: {node_elapsed:.2f}s")
        print(f"[Report Builder] Report compiled ({len(response.content)} chars).")

        # ── APPEND TIMING FOOTER TO REPORT ────────────────────────────────
        # Small metadata block appended to the bottom of the Markdown report.
        # Gives the user transparency on how long each component took.
        timing_footer = (
            f"\n\n---\n"
            f"*Report generated in **{node_elapsed:.1f}s** "
            f"(LLM: {llm_elapsed:.1f}s) · "
            f"{len(citation_map)} sources cited · "
            f"{len(state['raw_documents'])} document chunks retrieved*"
        )

        final_report = response.content + timing_footer

        return {
            **state,
            "final_report":   final_report,
            "current_agent":  "Report Builder ✅",
        }

    except Exception as e:
        node_elapsed = time.time() - node_start_time
        error_msg    = f"Report builder failed after {node_elapsed:.1f}s: {str(e)}"
        print(f"[Report Builder] ERROR: {error_msg}")

        return {
            **state,
            "final_report":  f"# Report Generation Failed\n\nError: {error_msg}",
            "current_agent": "Report Builder ❌",
            "error":         error_msg,
        }