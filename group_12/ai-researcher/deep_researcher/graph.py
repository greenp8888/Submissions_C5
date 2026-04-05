from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from .config import Settings
from .models import EvidenceItem, ResearchState
from .retrieval import (
    LOCAL_FILE_LABEL,
    build_arxiv_evidence,
    build_local_media_evidence,
    build_tavily_evidence,
    build_wikipedia_evidence,
)


def get_llm(settings: Settings, temperature: float = 0.2) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openrouter_model,
        openai_api_key=settings.openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=temperature,
        default_headers={
            "HTTP-Referer": "http://localhost:7860",
            "X-Title": "Local-Multi-Agent-Deep-Researcher",
        },
    )


def _append_trace(state: ResearchState, message: str) -> list[str]:
    return [*(state.get("trace", []) or []), message]


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _parallel_retrieval_timing(start: str) -> dict[str, str]:
    return {"start_utc": start, "end_utc": _utc_timestamp()}


def _format_parallel_timing_line(timing: dict[str, str] | None) -> str:
    if not timing:
        return "_Parallel retrieval timing not recorded for this channel._"
    s = str(timing.get("start_utc", "")).strip()
    e = str(timing.get("end_utc", "")).strip()
    if not s and not e:
        return "_Parallel retrieval timing not recorded for this channel._"
    return f"*Parallel retrieval (UTC) — **start:** `{s}` · **end:** `{e}`*"


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json|markdown|md)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _safe_json_loads(text: str) -> Any:
    try:
        return json.loads(_strip_code_fences(text))
    except Exception:
        return None


def _evidence_dedupe_key(item: EvidenceItem) -> tuple[Any, ...]:
    url = (item.get("url") or "").strip()
    if url:
        return ("url", url.lower())
    title = (item.get("title") or "").strip()[:240]
    ex = (item.get("excerpt") or "").strip()[:240]
    label = (item.get("source_label") or "").strip()
    return ("sig", label, title, ex)


def _dedupe_extend(existing: list[EvidenceItem], batch: list[EvidenceItem]) -> list[EvidenceItem]:
    seen: set[tuple[Any, ...]] = set()
    out: list[EvidenceItem] = []
    for item in existing:
        k = _evidence_dedupe_key(item)
        if k in seen:
            continue
        seen.add(k)
        out.append(item)
    for item in batch:
        k = _evidence_dedupe_key(item)
        if k in seen:
            continue
        seen.add(k)
        out.append(item)
    return out


def _normalize_followup_tool(token: str) -> str | None:
    t = (token or "").strip().lower()
    if t in ("local", "upload", "uploads", "pdf", "local uploads", "files"):
        return "local"
    if t in ("wikipedia", "wiki"):
        return "wikipedia"
    if t in ("arxiv", "arxiv.org", "papers"):
        return "arxiv"
    if t in ("tavily", "tavily web", "web", "internet", "search"):
        return "tavily"
    return None


def _retrieval_channel_enabled(state: ResearchState, channel: str) -> bool:
    flt = state.get("retrieval_tool_filter")
    if not flt:
        return True
    return channel in flt


_SOURCE_SECTION_INTROS: dict[str, str] = {
    "Tavily Web": "**Tavily (web search)** retrieved the following:",
    "Wikipedia": "**Wikipedia** contributed the following articles and summaries:",
    "arXiv": "**arXiv** contributed the following papers (abstract excerpts):",
    LOCAL_FILE_LABEL: "**Your uploaded files** (PDF, images, audio) yielded the following:",
}

# Labels we treat as standard tools (must match retrieval.py source_label values)
_TOOL_LABELS_ORDER = [LOCAL_FILE_LABEL, "Wikipedia", "arXiv", "Tavily Web"]


def _evidence_by_tool_label(evidence: list[EvidenceItem]) -> dict[str, list[EvidenceItem]]:
    by_label: dict[str, list[EvidenceItem]] = defaultdict(list)
    for item in evidence:
        label = (item.get("source_label") or item.get("source_type") or "Other").strip() or "Other"
        by_label[label].append(item)
    return by_label


def _bundle_excerpts_for_summary_prompt(evidence: list[EvidenceItem], max_items_per_tool: int = 8) -> str:
    """Compact excerpt text for one LLM call (per-tool summaries)."""
    groups = _evidence_by_tool_label(evidence)
    parts: list[str] = []
    for tool in _TOOL_LABELS_ORDER:
        items = groups.get(tool, [])
        parts.append(f"### {tool} ({len(items)} item(s))")
        if not items:
            parts.append("(No items retrieved.)")
            continue
        for i, item in enumerate(items[:max_items_per_tool], start=1):
            title = (item.get("title") or "Untitled").strip()
            excerpt = (item.get("excerpt") or "").strip()[:650]
            parts.append(f"{i}. Title: {title}\n   Excerpt: {excerpt}")
        if len(items) > max_items_per_tool:
            parts.append(f"... and {len(items) - max_items_per_tool} more item(s) omitted here.")
        parts.append("")
    other = [lb for lb in groups if lb not in _TOOL_LABELS_ORDER]
    for lb in sorted(other):
        parts.append(f"### Other: {lb}")
        for i, item in enumerate(groups[lb][:5], start=1):
            parts.append(f"{i}. {(item.get('title') or '')[:120]} — {(item.get('excerpt') or '')[:400]}")
        parts.append("")
    return "\n".join(parts).strip()


def llm_per_tool_source_summaries(
    llm: ChatOpenAI,
    question: str,
    evidence: list[EvidenceItem],
) -> dict[str, str]:
    """~100-word analytical paragraph per channel + Google/Tavily positioning."""
    bundle = _bundle_excerpts_for_summary_prompt(evidence)
    prompt = f"""
You are summarizing retrieval channels for a research report.

Research question:
{question}

Retrieved material (by tool):
{bundle}

Return strict JSON only, with this exact shape and string values. Each value must be ONE cohesive
paragraph of about 80–120 words (aim ~100 words), analytical not bullet points: what themes that
tool surfaced, how it helps answer the question, limits or blind spots, and how it complements other tools.
If that tool retrieved nothing, write one clear sentence stating that nothing was retrieved and why that matters.

For "google_search": this codebase does NOT call the Google Search API; open-web pages come from Tavily only.
Write ~100 words on what that means for coverage and how readers should interpret "web" results versus
a hypothetical direct Google search, without claiming Google was queried.

The "uploaded_pdf" key summarizes **local uploads** together: PDF text chunks, image captions (BLIP), and
audio transcripts (Whisper) when present — not only PDFs.

Keys (exactly):
{{
  "uploaded_pdf": "...",
  "wikipedia": "...",
  "arxiv": "...",
  "tavily_web": "...",
  "google_search": "..."
}}
""".strip()

    response = llm.invoke(prompt)
    content = getattr(response, "content", str(response))
    payload = _safe_json_loads(content)

    defaults = {
        "uploaded_pdf": "No local file evidence (PDF, image, or audio) was available to summarize.",
        "wikipedia": "No Wikipedia material was retrieved for this run.",
        "arxiv": "No arXiv papers were retrieved for this run.",
        "tavily_web": "No Tavily web results were retrieved for this run.",
        "google_search": (
            "This pipeline does not query Google Search directly; indexed web snippets are supplied by "
            "Tavily. Coverage reflects Tavily's crawl and ranking, not a full Google SERP, so niche or "
            "very recent pages may be missing compared with a manual Google search."
        ),
    }
    if not isinstance(payload, dict):
        return defaults

    out = dict(defaults)
    for key in out:
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            out[key] = val.strip()
    return out


def format_per_tool_analysis_markdown(
    summaries: dict[str, str],
    timings: dict[str, dict[str, str] | None],
) -> str:
    return "\n".join(
        [
            "### Analysis by retrieval tool (~100 words each)",
            "",
            "_Each paragraph synthesizes what that channel contributed; lengths are approximate._",
            "",
            "#### Local files — PDF, images, and audio",
            _format_parallel_timing_line(timings.get("uploaded_pdf")),
            "",
            summaries["uploaded_pdf"],
            "",
            "#### Wikipedia",
            _format_parallel_timing_line(timings.get("wikipedia")),
            "",
            summaries["wikipedia"],
            "",
            "#### arXiv",
            _format_parallel_timing_line(timings.get("arxiv")),
            "",
            summaries["arxiv"],
            "",
            "#### Web search — Tavily",
            _format_parallel_timing_line(timings.get("tavily_web")),
            "",
            summaries["tavily_web"],
            "",
            "#### Google Search (not queried — vs. Tavily web layer)",
            "_No parallel Google retriever in this pipeline; timing applies to Tavily above for web._",
            "",
            summaries["google_search"],
            "",
        ]
    ).strip()


def markdown_detailed_extracts_from_evidence(evidence: list[EvidenceItem]) -> str:
    """Numbered excerpts grouped by tool (under Sources appendix)."""
    if not evidence:
        return "_No row-level extracts — nothing was retrieved._"

    groups = _evidence_by_tool_label(evidence)
    ordered_labels = [lb for lb in _TOOL_LABELS_ORDER if lb in groups]
    ordered_labels.extend(sorted(lb for lb in groups if lb not in _TOOL_LABELS_ORDER))

    lines: list[str] = ["### Detailed extracts (all retrieved snippets)", ""]
    for label in ordered_labels:
        items = groups[label]
        intro = _SOURCE_SECTION_INTROS.get(label, f"**{label}** contributed the following:")
        lines.append(f"#### {label}")
        lines.append(intro)
        lines.append("")
        for idx, item in enumerate(items, start=1):
            title = (item.get("title") or "Untitled").strip()
            url = (item.get("url") or "").strip()
            excerpt = (item.get("excerpt") or "").strip()
            query = (item.get("query_used") or "").strip()
            head = f"{idx}. **{title}**"
            if url:
                head += f" — [link]({url})"
            lines.append(head)
            if query:
                lines.append(f"   - *Query used:* {query}")
            if excerpt:
                lines.append(f"   - *Extracted text:* {excerpt}")
            else:
                lines.append("   - *Extracted text:* _(empty)_")
            lines.append("")
    return "\n".join(lines).rstrip()


def markdown_references_all_sources(evidence: list[EvidenceItem]) -> str:
    """Flat list of every distinct source from retrieval (for bibliography-style use)."""
    lines: list[str] = [
        "## References (all search sources)",
        "",
        "_Every distinct item merged from local files (PDF/image/audio), Wikipedia, arXiv, and Tavily._",
        "",
    ]
    if not evidence:
        lines.append("_No sources recorded._")
        return "\n".join(lines)

    seen: set[tuple[str, str, str]] = set()
    n = 0
    for item in evidence:
        label = (item.get("source_label") or item.get("source_type") or "Source").strip()
        title = (item.get("title") or "Untitled").strip()
        url = (item.get("url") or "").strip()
        key = (label, title, url)
        if key in seen:
            continue
        seen.add(key)
        n += 1
        if url:
            lines.append(f"{n}. **[{label}]** {title} — {url}")
        else:
            lines.append(f"{n}. **[{label}]** {title}")

    return "\n".join(lines)


def markdown_sources_analysis_only(
    evidence: list[EvidenceItem],
    summaries: dict[str, str],
    timings: dict[str, dict[str, str] | None],
) -> str:
    """Sources section for the main report: per-tool ~100-word analysis only (no row-level extracts)."""
    analysis = format_per_tool_analysis_markdown(summaries, timings)
    return "\n\n".join(
        [
            "## Sources and extracted information",
            "",
            analysis,
            "",
            "_Row-level **Detailed extracts** also appear in the **Sources** tab in the Gradio UI._",
        ]
    ).strip()


def planner_node(state: ResearchState, settings: Settings) -> dict:
    llm = get_llm(settings, temperature=0.1)
    prompt = f"""
You are the Research Planner agent in a multi-agent deep research system.

Break the user's question into 4 to 6 sub-questions that will help a retriever gather evidence.
Return strict JSON with this exact shape:
{{
  "objective": "...",
  "subquestions": ["...", "..."]
}}

User question:
{state["question"]}
""".strip()

    response = llm.invoke(prompt)
    content = getattr(response, "content", str(response))
    payload = _safe_json_loads(content)

    subquestions: list[str]
    if isinstance(payload, dict) and isinstance(payload.get("subquestions"), list):
        subquestions = [str(x).strip() for x in payload["subquestions"] if str(x).strip()]
    else:
        subquestions = [
            line.strip("-•1234567890. ").strip()
            for line in content.splitlines()
            if line.strip()
        ]
        subquestions = [line for line in subquestions if len(line) > 10][:6]

    if not subquestions:
        subquestions = [state["question"]]

    objective = ""
    if isinstance(payload, dict):
        objective = str(payload.get("objective", "") or "").strip()

    trace_msg = f"Planner created {len(subquestions)} sub-question(s)."
    if objective:
        trace_msg += f" Objective: {objective[:200]}{'…' if len(objective) > 200 else ''}"

    out: dict[str, Any] = {
        "subquestions": subquestions,
        "trace": _append_trace(state, trace_msg),
    }
    if objective:
        out["research_objective"] = objective
    return out


def prep_retrieval_node(state: ResearchState) -> dict:
    queries = [state["question"], *(state.get("subquestions", []) or [])]
    return {
        "queries": queries,
        "retrieval_tool_filter": None,
        "trace": _append_trace(
            state,
            f"Prepared {len(queries)} retrieval quer(ies) (question + sub-questions).",
        ),
    }


# Parallel retrieval nodes (one per source)
def local_media_retriever_node(state: ResearchState, settings: Settings) -> dict:
    t0 = _utc_timestamp()
    if not _retrieval_channel_enabled(state, "local"):
        return {
            "local_media_evidence": [],
            "retrieval_log": ["[local_media] Skipped for this wave (tool filter)."],
            "retrieval_timing_local_media": _parallel_retrieval_timing(t0),
        }
    paths = state.get("local_file_paths", []) or []
    queries = state.get("queries", [])
    top_k = int(state.get("top_k", settings.top_k))

    if not paths:
        return {
            "local_media_evidence": [],
            "retrieval_log": ["[local_media] No files uploaded; skipping local PDF/image/audio retrieval."],
            "retrieval_timing_local_media": _parallel_retrieval_timing(t0),
        }
    if not queries:
        return {
            "local_media_evidence": [],
            "retrieval_log": ["[local_media] No queries in state; skipping."],
            "retrieval_timing_local_media": _parallel_retrieval_timing(t0),
        }
    try:
        media_evidence, status_note = build_local_media_evidence(
            file_paths=paths,
            queries=queries,
            embedding_model=settings.embedding_model,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            top_k=top_k,
            research_question=state["question"],
            parallel_workers=settings.max_workers_pdf_io,
            asr_model_id=settings.asr_hf_model,
            asr_max_seconds=settings.asr_max_seconds,
        )
        return {
            "local_media_evidence": media_evidence,
            "retrieval_log": [
                f"[local_media] {len(paths)} path(s), top_k={top_k}, {status_note}."
            ],
            "retrieval_timing_local_media": _parallel_retrieval_timing(t0),
        }
    except Exception as exc:
        return {
            "local_media_evidence": [],
            "retrieval_log": [f"[local_media] Error: {exc!s}"],
            "retrieval_timing_local_media": _parallel_retrieval_timing(t0),
        }


def wikipedia_retriever_node(state: ResearchState, settings: Settings) -> dict:
    t0 = _utc_timestamp()
    if not _retrieval_channel_enabled(state, "wikipedia"):
        return {
            "wikipedia_evidence": [],
            "retrieval_log": ["[wikipedia_retriever] Skipped for this wave (tool filter)."],
            "retrieval_timing_wikipedia": _parallel_retrieval_timing(t0),
        }
    queries = state.get("queries", [])
    if not queries:
        return {
            "wikipedia_evidence": [],
            "retrieval_log": ["[wikipedia_retriever] No queries in state; skipping."],
            "retrieval_timing_wikipedia": _parallel_retrieval_timing(t0),
        }
    try:
        wikipedia_evidence = build_wikipedia_evidence(queries)
    except Exception as exc:
        return {
            "wikipedia_evidence": [],
            "retrieval_log": [f"[wikipedia_retriever] Error: {exc!s}"],
            "retrieval_timing_wikipedia": _parallel_retrieval_timing(t0),
        }
    msg = (
        f"[wikipedia_retriever] Collected {len(wikipedia_evidence)} Wikipedia page(s) "
        f"from {len(queries)} quer(ies)."
    )
    if not wikipedia_evidence:
        msg += " (no pages resolved — network, disambiguation, or empty search results.)"
    return {
        "wikipedia_evidence": wikipedia_evidence,
        "retrieval_log": [msg],
        "retrieval_timing_wikipedia": _parallel_retrieval_timing(t0),
    }


def arxiv_retriever_node(state: ResearchState, settings: Settings) -> dict:
    t0 = _utc_timestamp()
    if not _retrieval_channel_enabled(state, "arxiv"):
        return {
            "arxiv_evidence": [],
            "retrieval_log": ["[arxiv_retriever] Skipped for this wave (tool filter)."],
            "retrieval_timing_arxiv": _parallel_retrieval_timing(t0),
        }
    queries = state.get("queries", [])
    if not queries:
        return {
            "arxiv_evidence": [],
            "retrieval_log": ["[arxiv_retriever] No queries in state; skipping."],
            "retrieval_timing_arxiv": _parallel_retrieval_timing(t0),
        }
    try:
        arxiv_evidence = build_arxiv_evidence(queries, max_results_per_query=3)
    except Exception as exc:
        return {
            "arxiv_evidence": [],
            "retrieval_log": [f"[arxiv_retriever] Error: {exc!s}"],
            "retrieval_timing_arxiv": _parallel_retrieval_timing(t0),
        }
    msg = (
        f"[arxiv_retriever] Collected {len(arxiv_evidence)} paper(s) "
        f"from {len(queries)} quer(ies) (max 3 hits per query attempt)."
    )
    if not arxiv_evidence:
        msg += " (arXiv search returned nothing or failed per query.)"
    return {
        "arxiv_evidence": arxiv_evidence,
        "retrieval_log": [msg],
        "retrieval_timing_arxiv": _parallel_retrieval_timing(t0),
    }


def tavily_retriever_node(state: ResearchState, settings: Settings) -> dict:
    t0 = _utc_timestamp()
    if not _retrieval_channel_enabled(state, "tavily"):
        return {
            "tavily_evidence": [],
            "retrieval_log": ["[tavily_retriever] Skipped for this wave (tool filter)."],
            "retrieval_timing_tavily": _parallel_retrieval_timing(t0),
        }
    queries = state.get("queries", [])
    web_results_per_query = int(state.get("web_results_per_query", settings.web_results_per_query))

    if not state.get("enable_web_search", True):
        return {
            "tavily_evidence": [],
            "retrieval_log": ["[tavily_retriever] Web search disabled in UI; skipping Tavily."],
            "retrieval_timing_tavily": _parallel_retrieval_timing(t0),
        }
    if not settings.tavily_api_key:
        return {
            "tavily_evidence": [],
            "retrieval_log": ["[tavily_retriever] TAVILY_API_KEY not set; skipping web search."],
            "retrieval_timing_tavily": _parallel_retrieval_timing(t0),
        }
    if not queries:
        return {
            "tavily_evidence": [],
            "retrieval_log": ["[tavily_retriever] No queries in state; skipping."],
            "retrieval_timing_tavily": _parallel_retrieval_timing(t0),
        }
    try:
        tavily_evidence = build_tavily_evidence(
            api_key=settings.tavily_api_key,
            queries=queries,
            max_results_per_query=web_results_per_query,
        )
    except Exception as exc:
        return {
            "tavily_evidence": [],
            "retrieval_log": [f"[tavily_retriever] Error: {exc!s}"],
            "retrieval_timing_tavily": _parallel_retrieval_timing(t0),
        }
    msg = (
        f"[tavily_retriever] Collected {len(tavily_evidence)} web result(s) "
        f"from {len(queries)} quer(ies), max_results_per_query={web_results_per_query}."
    )
    if not tavily_evidence:
        msg += " (empty response or Tavily client/import issue.)"
    return {
        "tavily_evidence": tavily_evidence,
        "retrieval_log": [msg],
        "retrieval_timing_tavily": _parallel_retrieval_timing(t0),
    }


def retriever_merge_node(state: ResearchState, settings: Settings) -> dict:
    """Initial merge: replace corpus with this wave's parallel retriever outputs."""
    batch: list[EvidenceItem] = []

    loc_n = len(state.get("local_media_evidence", []) or [])
    wiki_n = len(state.get("wikipedia_evidence", []) or [])
    arx_n = len(state.get("arxiv_evidence", []) or [])
    tav_n = len(state.get("tavily_evidence", []) or [])

    batch.extend(state.get("local_media_evidence", []) or [])
    batch.extend(state.get("wikipedia_evidence", []) or [])
    batch.extend(state.get("arxiv_evidence", []) or [])
    batch.extend(state.get("tavily_evidence", []) or [])

    evidence = list(batch)
    cap = int(settings.max_evidence_items)
    trimmed = 0
    if len(evidence) > cap:
        trimmed = len(evidence) - cap
        evidence = evidence[-cap:]

    log_lines = [
        "[retriever_merge] Initial wave: "
        f"Local={loc_n}, Wikipedia={wiki_n}, arXiv={arx_n}, Tavily={tav_n} → total {len(evidence)}."
    ]
    if trimmed:
        log_lines.append(
            f"[retriever_merge] Trimmed {trimmed} item(s) to respect max_evidence_items={cap}."
        )

    return {
        "evidence": evidence,
        "retrieval_log": log_lines,
        "trace": _append_trace(
            state,
            f"Retriever merge (initial wave): {len(evidence)} evidence item(s) in corpus.",
        ),
    }


def retriever_merge_followup_node(state: ResearchState, settings: Settings) -> dict:
    """Follow-up merge: append deduped batch to existing evidence (separate LangGraph node from initial merge)."""
    batch: list[EvidenceItem] = []

    loc_n = len(state.get("local_media_evidence", []) or [])
    wiki_n = len(state.get("wikipedia_evidence", []) or [])
    arx_n = len(state.get("arxiv_evidence", []) or [])
    tav_n = len(state.get("tavily_evidence", []) or [])

    batch.extend(state.get("local_media_evidence", []) or [])
    batch.extend(state.get("wikipedia_evidence", []) or [])
    batch.extend(state.get("arxiv_evidence", []) or [])
    batch.extend(state.get("tavily_evidence", []) or [])

    prior = list(state.get("evidence", []) or [])
    evidence = _dedupe_extend(prior, batch)
    cap = int(settings.max_evidence_items)
    trimmed = 0
    if len(evidence) > cap:
        trimmed = len(evidence) - cap
        evidence = evidence[-cap:]

    ap = int(state.get("analyst_pass_count", 0))
    log_lines = [
        "[retriever_merge_followup] Follow-up wave after analyst pass "
        f"{ap}: Local={loc_n}, Wikipedia={wiki_n}, arXiv={arx_n}, Tavily={tav_n} "
        f"→ +batch {len(batch)} → corpus {len(evidence)}."
    ]
    if trimmed:
        log_lines.append(
            f"[retriever_merge_followup] Trimmed {trimmed} oldest item(s) to max_evidence_items={cap}."
        )

    return {
        "evidence": evidence,
        "retrieval_log": log_lines,
        "trace": _append_trace(
            state,
            f"Follow-up retriever merge: {len(evidence)} evidence item(s) in corpus.",
        ),
    }


def analyst_node(state: ResearchState, settings: Settings) -> dict:
    llm = get_llm(settings, temperature=0.1)
    evidence = state.get("evidence", [])
    pass_n = int(state.get("analyst_pass_count", 0)) + 1

    if not evidence:
        summary = (
            "No evidence was retrieved. The report should explicitly state that the "
            "research run had insufficient supporting material."
        )
        return {
            "analysis_summary": summary,
            "contradictions": [],
            "analyst_pass_count": pass_n,
            "trace": _append_trace(
                state,
                f"Critical Analyst (pass {pass_n}) found no evidence to assess.",
            ),
        }

    limit = int(settings.analyst_evidence_limit)
    window = evidence[-limit:] if len(evidence) > limit else evidence

    evidence_block = "\n\n".join(
        [
            (
                f"[{idx}] {item['source_label']} | {item['title']}\n"
                f"URL: {item['url'] or 'n/a'}\n"
                f"Excerpt: {item['excerpt']}"
            )
            for idx, item in enumerate(window, start=1)
        ]
    )

    prompt = f"""
You are the Critical Analysis agent in a multi-agent deep research system.

Analyze the evidence and return strict JSON with this exact shape:
{{
  "analysis_summary": "...",
  "contradictions": ["...", "..."],
  "quality_notes": ["...", "..."]
}}

Research question:
{state["question"]}

Evidence:
{evidence_block}
""".strip()

    response = llm.invoke(prompt)
    content = getattr(response, "content", str(response))
    payload = _safe_json_loads(content)

    if isinstance(payload, dict):
        analysis_summary = str(payload.get("analysis_summary", "")).strip() or content
        contradictions = [
            str(x).strip() for x in payload.get("contradictions", []) if str(x).strip()
        ]
        quality_notes = [str(x).strip() for x in payload.get("quality_notes", []) if str(x).strip()]
    else:
        analysis_summary = content
        contradictions = []
        quality_notes = []

    if quality_notes:
        analysis_summary += "\n\nEvidence quality notes:\n" + "\n".join(f"- {x}" for x in quality_notes)

    if len(evidence) > len(window):
        analysis_summary += (
            f"\n\n_Note: Analyst viewed the last {len(window)} of {len(evidence)} evidence items "
            "(most recent / end of corpus)._"
        )

    return {
        "analysis_summary": analysis_summary,
        "contradictions": contradictions,
        "analyst_pass_count": pass_n,
        "trace": _append_trace(
            state,
            f"Critical Analyst (pass {pass_n}) produced {len(contradictions)} contradiction note(s).",
        ),
    }


def gap_planner_node(state: ResearchState, settings: Settings) -> dict:
    llm = get_llm(settings, temperature=0.15)
    max_r = min(2, max(1, int(state.get("max_research_rounds", settings.max_research_rounds))))
    passes = int(state.get("analyst_pass_count", 0))
    if max_r <= 1 or passes >= max_r:
        return {}

    evidence = state.get("evidence", []) or []
    by_label = _evidence_by_tool_label(evidence)
    counts = ", ".join(f"{lb}: {len(items)}" for lb, items in sorted(by_label.items())) or "none"

    titles = "\n".join(
        f"- {(item.get('title') or '')[:120]}" for item in evidence[:12]
    ) or "- (none)"

    objective = (state.get("research_objective") or "").strip()
    obj_line = f"Planner objective:\n{objective}\n" if objective else ""

    prompt = f"""
You are the Gap Planning agent in a multi-agent deep research system.

The user may run up to {max_r} analyst passes total. The critical analyst has just finished pass {passes}.
If another retrieval wave is warranted before the final report, propose focused follow-up queries.

Return strict JSON only with this exact shape:
{{
  "gaps": ["...", "..."],
  "followup_queries": ["...", "..."],
  "tools": ["local", "wikipedia", "arxiv", "tavily"]
}}

Rules:
- Propose 2 to {settings.max_followup_queries} followup_queries (short, search-ready). Use [] if evidence is already sufficient.
- "tools" lists which retrieval channels to use for the follow-up wave. Use any subset of:
  "local", "wikipedia", "arxiv", "tavily". If unsure, include all relevant channels.
- Respect that Tavily/web may be disabled in the app: still include "tavily" if web would help; the runtime will no-op if off.
- "gaps" should name concrete missing angles, conflicts to resolve, or depth needed (3-6 strings).

{obj_line}Research question:
{state["question"]}

Subquestions:
{chr(10).join(f"- {x}" for x in state.get("subquestions", []) or [])}

Analyst summary:
{state.get("analysis_summary", "")}

Contradictions:
{chr(10).join(state.get("contradictions", []) or ["None noted"])}

Evidence counts by label: {counts}

Sample titles:
{titles}
""".strip()

    response = llm.invoke(prompt)
    content = getattr(response, "content", str(response))
    payload = _safe_json_loads(content)

    gaps: list[str] = []
    followup_queries: list[str] = []
    tools_raw: list[str] = []

    if isinstance(payload, dict):
        if isinstance(payload.get("gaps"), list):
            gaps = [str(x).strip() for x in payload["gaps"] if str(x).strip()]
        if isinstance(payload.get("followup_queries"), list):
            followup_queries = [
                str(x).strip() for x in payload["followup_queries"] if str(x).strip()
            ]
        if isinstance(payload.get("tools"), list):
            tools_raw = [str(x).strip() for x in payload["tools"] if str(x).strip()]

    cap = int(settings.max_followup_queries)
    followup_queries = followup_queries[:cap]

    normalized_tools: list[str] = []
    for t in tools_raw:
        n = _normalize_followup_tool(t)
        if n and n not in normalized_tools:
            normalized_tools.append(n)

    round_md_parts: list[str] = [
        f"#### Gap planning after analyst pass {passes}",
        "",
        "**Gaps identified:**",
    ]
    if gaps:
        round_md_parts.extend(f"- {g}" for g in gaps)
    else:
        round_md_parts.append("- _(none listed)_")
    round_md_parts.extend(
        [
            "",
            "**Planned follow-up queries:**",
        ]
    )
    if followup_queries:
        round_md_parts.extend(f"- {q}" for q in followup_queries)
    else:
        round_md_parts.append("- _(none — stopping additional retrieval)_")
    round_md_parts.extend(
        [
            "",
            f"**Tools suggested:** {', '.join(normalized_tools) if normalized_tools else '_(default: all channels)_'}",
            "",
        ]
    )

    return {
        "gap_findings": gaps,
        "followup_queries": followup_queries,
        "followup_tools": normalized_tools,
        "gap_round_log": ["\n".join(round_md_parts).strip()],
        "trace": _append_trace(
            state,
            f"Gap planner proposed {len(followup_queries)} follow-up quer(ies) after pass {passes}.",
        ),
    }


def prep_followup_retrieval_node(state: ResearchState, settings: Settings) -> dict:
    raw = state.get("followup_queries") or []
    cap = int(settings.max_followup_queries)
    queries = [str(q).strip() for q in raw if str(q).strip()][:cap]

    tools = list(state.get("followup_tools") or [])
    allowed: list[str] = []
    for x in tools:
        n = _normalize_followup_tool(str(x))
        if n and n not in allowed:
            allowed.append(n)
    if not allowed:
        allowed = ["local", "wikipedia", "arxiv", "tavily"]

    return {
        "queries": queries,
        "retrieval_tool_filter": allowed,
        "trace": _append_trace(
            state,
            f"Follow-up retrieval: {len(queries)} quer(ies); channels={allowed}.",
        ),
    }


def route_after_analyst(state: ResearchState) -> str:
    """First analyst only: skip gap when single-pass; else go to gap planner."""
    max_r = min(2, max(1, int(state.get("max_research_rounds", 1))))
    passes = int(state.get("analyst_pass_count", 0))
    if max_r <= 1:
        return "insight_direct"
    if passes >= max_r:
        return "insight_direct"
    return "gap_planner"


def route_after_gap(state: ResearchState) -> str:
    """After gap planner: stop if no queries; else run one follow-up retrieval wave (max 2 analyst passes)."""
    passes = int(state.get("analyst_pass_count", 0))
    max_r = min(2, max(1, int(state.get("max_research_rounds", 1))))
    if passes >= max_r:
        return "insight_post_gap_skip"
    qs = state.get("followup_queries") or []
    if not qs:
        return "insight_post_gap_skip"
    return "prep_followup"


def insight_node(state: ResearchState, settings: Settings) -> dict:
    llm = get_llm(settings, temperature=0.3)
    prompt = f"""
You are the Insight Generation agent in a multi-agent deep research system.

Using the research question, the evidence, and the analyst summary, produce 3 to 6 concise insights.
These may include trends, implications, open hypotheses, or practical next steps.

Return strict JSON with this shape:
{{
  "insights": ["...", "..."]
}}

Research question:
{state["question"]}

Analyst summary:
{state.get("analysis_summary", "")}

Contradictions:
{chr(10).join(state.get("contradictions", []) or ['None noted'])}
""".strip()

    response = llm.invoke(prompt)
    content = getattr(response, "content", str(response))
    payload = _safe_json_loads(content)

    if isinstance(payload, dict) and isinstance(payload.get("insights"), list):
        insights = [str(x).strip() for x in payload["insights"] if str(x).strip()]
    else:
        insights = [
            line.strip("-•1234567890. ").strip()
            for line in content.splitlines()
            if line.strip()
        ]
        insights = [line for line in insights if len(line) > 10][:6]

    return {
        "insights": insights,
        "trace": _append_trace(
            state,
            f"Insight Generator produced {len(insights)} insight(s).",
        ),
    }


def report_node(state: ResearchState, settings: Settings) -> dict:
    llm = get_llm(settings, temperature=0.2)

    evidence = state.get("evidence", [])
    evidence_catalog = "\n".join(
        [
            f"- {item['source_label']}: {item['title']} ({item['url'] or 'no external URL'})"
            for item in evidence[:25]
        ]
    ) or "- No evidence collected"

    insights_block = "\n".join(f"- {x}" for x in state.get("insights", []) or ["No insights generated"])
    contradictions_block = "\n".join(
        f"- {x}" for x in state.get("contradictions", []) or ["No explicit contradictions identified"]
    )

    analyst_passes = int(state.get("analyst_pass_count", 0))
    multi_pass_note = ""
    if analyst_passes > 1:
        multi_pass_note = (
            f"\nThe pipeline completed **{analyst_passes} critical-analyst passes** with optional "
            "follow-up retrieval between passes. Add a concise subsection **Multi-pass research** "
            "stating that a second evidence wave was merged when applicable and how that changed confidence "
            "or coverage (or say follow-up added no new material if that fits the evidence).\n"
        )

    prompt = f"""
You are the Report Builder agent in a multi-agent deep research system.

The final document already begins with **Sources and extracted information** (~100-word analyses per tool
only; full row-level extracts are optional in the UI) and ends with **References (all search sources)**.
Do not paste long excerpts, duplicate the reference list, or re-hash the per-tool analysis paragraphs.

Write a polished markdown report (this part sits **between** those blocks) with these sections only:
1. Research Question
2. Research Plan
3. Evidence Collected (thematic synthesis — no long quotes)
4. Critical Findings
5. Contradictions / Caveats
6. Insights / Hypotheses
7. Conclusion
{multi_pass_note}
The report must be practical, honest about uncertainty, and easy to demo.

Research question:
{state["question"]}

Subquestions:
{chr(10).join(f"- {x}" for x in state.get("subquestions", []))}

Evidence catalog:
{evidence_catalog}

Critical findings:
{state.get("analysis_summary", "")}

Contradictions:
{contradictions_block}

Insights:
{insights_block}
""".strip()

    response = llm.invoke(prompt)
    narrative = getattr(response, "content", str(response)).strip()

    summary_llm = get_llm(settings, temperature=0.15)
    per_tool = llm_per_tool_source_summaries(summary_llm, state["question"], evidence)
    retrieval_timings: dict[str, dict[str, str] | None] = {
        "uploaded_pdf": state.get("retrieval_timing_local_media"),
        "wikipedia": state.get("retrieval_timing_wikipedia"),
        "arxiv": state.get("retrieval_timing_arxiv"),
        "tavily_web": state.get("retrieval_timing_tavily"),
        "google_search": None,
    }
    sources_block = markdown_sources_analysis_only(evidence, per_tool, retrieval_timings)
    detailed_md = markdown_detailed_extracts_from_evidence(evidence)
    references_block = markdown_references_all_sources(evidence)

    final_report = "\n\n".join(
        [
            sources_block,
            "---",
            narrative,
            "---",
            references_block,
        ]
    )

    return {
        "final_report": final_report,
        "detailed_extracts_markdown": detailed_md,
        "trace": _append_trace(state, "Report Builder assembled the final markdown report."),
    }


def build_graph(settings: Settings):
    graph = StateGraph(ResearchState)
    
    # Add nodes
    graph.add_node("planner", lambda state: planner_node(state, settings))
    
    graph.add_node("prep_retrieval", prep_retrieval_node)
    
    # Parallel retrieval nodes
    graph.add_node("local_media_retriever", lambda state: local_media_retriever_node(state, settings))
    graph.add_node("wikipedia_retriever", lambda state: wikipedia_retriever_node(state, settings))
    graph.add_node("arxiv_retriever", lambda state: arxiv_retriever_node(state, settings))
    graph.add_node("tavily_retriever", lambda state: tavily_retriever_node(state, settings))
    
    # Merge retrieval results (initial vs follow-up are separate LangGraph nodes to avoid fan-in deadlock)
    graph.add_node("retriever_merge", lambda state: retriever_merge_node(state, settings))
    graph.add_node("retriever_merge_followup", lambda state: retriever_merge_followup_node(state, settings))

    # Follow-up retrievers reuse the same node functions but distinct graph nodes (parallel only to each other)
    graph.add_node("local_media_retriever_f", lambda state: local_media_retriever_node(state, settings))
    graph.add_node("wikipedia_retriever_f", lambda state: wikipedia_retriever_node(state, settings))
    graph.add_node("arxiv_retriever_f", lambda state: arxiv_retriever_node(state, settings))
    graph.add_node("tavily_retriever_f", lambda state: tavily_retriever_node(state, settings))
    
    # Analysis nodes
    graph.add_node("critical_analyst", lambda state: analyst_node(state, settings))
    graph.add_node("gap_planner", lambda state: gap_planner_node(state, settings))
    graph.add_node("prep_followup", lambda state: prep_followup_retrieval_node(state, settings))
    # Separate insight/report chains avoid LangGraph multi-parent deadlock on shared nodes
    graph.add_node("insight_direct", lambda state: insight_node(state, settings))
    graph.add_node("insight_post_gap_skip", lambda state: insight_node(state, settings))
    graph.add_node("insight_post_followup", lambda state: insight_node(state, settings))
    graph.add_node("report_direct", lambda state: report_node(state, settings))
    graph.add_node("report_post_gap_skip", lambda state: report_node(state, settings))
    graph.add_node("report_post_followup", lambda state: report_node(state, settings))
    graph.add_node("critical_analyst_followup", lambda state: analyst_node(state, settings))
    
    # Edges
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "prep_retrieval")
    
    # All retriever nodes run in parallel (fan-out)
    graph.add_edge("prep_retrieval", "local_media_retriever")
    graph.add_edge("prep_retrieval", "wikipedia_retriever")
    graph.add_edge("prep_retrieval", "arxiv_retriever")
    graph.add_edge("prep_retrieval", "tavily_retriever")

    # Follow-up wave: dedicated retriever nodes → dedicated merge (append + dedupe)
    graph.add_edge("prep_followup", "local_media_retriever_f")
    graph.add_edge("prep_followup", "wikipedia_retriever_f")
    graph.add_edge("prep_followup", "arxiv_retriever_f")
    graph.add_edge("prep_followup", "tavily_retriever_f")

    graph.add_edge("local_media_retriever_f", "retriever_merge_followup")
    graph.add_edge("wikipedia_retriever_f", "retriever_merge_followup")
    graph.add_edge("arxiv_retriever_f", "retriever_merge_followup")
    graph.add_edge("tavily_retriever_f", "retriever_merge_followup")
    
    # Initial merge after first parallel wave
    graph.add_edge("local_media_retriever", "retriever_merge")
    graph.add_edge("wikipedia_retriever", "retriever_merge")
    graph.add_edge("arxiv_retriever", "retriever_merge")
    graph.add_edge("tavily_retriever", "retriever_merge")
    
    # First analyst only from initial merge (follow-up merge feeds a separate analyst node — no dual fan-in)
    graph.add_edge("retriever_merge", "critical_analyst")
    graph.add_edge("retriever_merge_followup", "critical_analyst_followup")
    graph.add_conditional_edges(
        "critical_analyst",
        route_after_analyst,
        {
            "insight_direct": "insight_direct",
            "gap_planner": "gap_planner",
        },
    )
    graph.add_conditional_edges(
        "gap_planner",
        route_after_gap,
        {
            "insight_post_gap_skip": "insight_post_gap_skip",
            "prep_followup": "prep_followup",
        },
    )
    graph.add_edge("critical_analyst_followup", "insight_post_followup")
    graph.add_edge("insight_direct", "report_direct")
    graph.add_edge("insight_post_gap_skip", "report_post_gap_skip")
    graph.add_edge("insight_post_followup", "report_post_followup")
    graph.add_edge("report_direct", END)
    graph.add_edge("report_post_gap_skip", END)
    graph.add_edge("report_post_followup", END)

    return graph.compile()