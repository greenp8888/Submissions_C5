"""
Shared research orchestration for Streamlit (no Gradio imports).

Reuses the same LangGraph pipeline and preflight as ``app.py``.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from deep_researcher.config import Settings
from deep_researcher.graph import build_graph, normalize_excerpt_whitespace
from deep_researcher.preflight import assemble_preflight_markdown, build_upload_digest, llm_preflight_analysis


def settings_from_ui(
    llm_provider: str,
    openrouter_key: str,
    openrouter_model: str,
    anthropic_key: str,
    anthropic_model: str,
) -> Settings:
    return Settings.load(
        llm_provider_override=(llm_provider or "").strip() or None,
        openrouter_api_key_override=(openrouter_key or "").strip() or None,
        openrouter_model_override=(openrouter_model or "").strip() or None,
        anthropic_api_key_override=(anthropic_key or "").strip() or None,
        anthropic_model_override=(anthropic_model or "").strip() or None,
    )


def trace_to_markdown(trace: list[str], retrieval_log: list[str] | None = None) -> str:
    sections: list[str] = []
    if trace:
        sections.append("**Orchestration**\n" + "\n".join(f"- {item}" for item in trace))
    log = retrieval_log or []
    if log:
        sections.append("**Retrieval**\n" + "\n".join(f"- {item}" for item in log))
    if not sections:
        return "_No trace available._"
    return "\n\n".join(sections)


def format_live_progress(state: dict) -> str:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    lines = [
        "## Live pipeline progress",
        "",
        f"_Updated {ts}_",
        "",
        "### Orchestration",
    ]
    for item in state.get("trace") or []:
        lines.append(f"- {item}")
    rlog = state.get("retrieval_log") or []
    if rlog:
        lines.extend(["", "### Retrieval log"])
        for item in rlog:
            lines.append(f"- {item}")
    gaps = state.get("gap_round_log") or []
    if gaps:
        lines.extend(["", "### Gap planner (recent)"])
        for item in gaps[-6:]:
            s = str(item)
            lines.append(f"- {s[:500]}{'…' if len(s) > 500 else ''}")
    return "\n".join(lines)


def evidence_to_dataframe(evidence: list[dict], excerpt_max: int = 320) -> pd.DataFrame:
    if not evidence:
        return pd.DataFrame(
            columns=[
                "source_type",
                "source_label",
                "title",
                "url",
                "excerpt",
                "query_used",
                "relevance_hint",
            ]
        )
    rows = []
    for item in evidence:
        ex = normalize_excerpt_whitespace(item.get("excerpt") or "")
        if len(ex) > excerpt_max:
            ex = ex[: excerpt_max - 1] + "…"
        rows.append(
            {
                "source_type": item.get("source_type", ""),
                "source_label": item.get("source_label", ""),
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "excerpt": ex,
                "query_used": item.get("query_used", ""),
                "relevance_hint": item.get("relevance_hint", ""),
            }
        )
    return pd.DataFrame(rows)


def format_gaps_markdown(gap_round_log: list[str] | None) -> str:
    logs = gap_round_log or []
    if not logs:
        return (
            "_No gap-planning output yet. Use **Analyst passes** = 2 to enable a follow-up "
            "retrieval wave after the first critical analysis._"
        )
    return "\n\n---\n\n".join(logs)


def format_objective_markdown(objective: str | None) -> str:
    o = (objective or "").strip()
    if not o:
        return "_The planner did not return a separate objective line (check trace)._"
    return f"**Planner objective:** {o}"


def finalize_research_outputs(result: dict) -> tuple[str, str, str, pd.DataFrame, str, str, str, str]:
    """Returns report, gaps_md, objective_md, evidence_df, trace_md, contradictions_md, full_md, sources_detail."""
    report = result.get("final_report", "No report was generated.")
    detailed_md = (result.get("detailed_extracts_markdown") or "").strip()
    evidence_df = evidence_to_dataframe(result.get("evidence", []))
    trace_md = trace_to_markdown(result.get("trace", []), result.get("retrieval_log"))
    contradictions = result.get("contradictions", []) or []
    contradictions_md = "\n".join(f"- {item}" for item in contradictions) or "_No explicit contradictions noted._"
    gaps_md = format_gaps_markdown(result.get("gap_round_log"))
    objective_md = format_objective_markdown(result.get("research_objective"))
    download_markdown = (
        f"{report}\n\n---\n\n## Detailed extracts\n\n{detailed_md}" if detailed_md else report
    )
    sources_detail = detailed_md or "_No detailed extracts (nothing retrieved)._"
    return (
        report,
        gaps_md,
        objective_md,
        evidence_df,
        trace_md,
        contradictions_md,
        download_markdown,
        sources_detail,
    )


def derive_title(report_md: str, question: str) -> str:
    for line in (report_md or "").splitlines():
        line = line.strip()
        if line.startswith("#"):
            t = line.lstrip("#").strip()
            if t:
                return t[:120]
    q = (question or "").strip()
    if not q:
        return "Untitled research"
    return q[:80] + ("…" if len(q) > 80 else "")


def slug_filename_base(title: str, max_len: int = 48) -> str:
    s = re.sub(r"[^\w\s-]", "", (title or "research").lower())
    s = re.sub(r"[-\s]+", "-", s).strip("-") or "research"
    return s[:max_len]


def write_artifact_markdown(base_dir: Path, base_name: str, markdown_text: str) -> Path:
    base_dir.mkdir(parents=True, exist_ok=True)
    path = base_dir / f"{base_name}.md"
    path.write_text(markdown_text, encoding="utf-8")
    return path


def markdown_to_pdf_bytes(md_text: str) -> bytes | None:
    """Return PDF bytes, or None if optional deps are missing."""
    try:
        import markdown as md_lib
        from xhtml2pdf import pisa
    except ImportError:
        return None
    html_body = md_lib.markdown(md_text or "", extensions=["tables", "fenced_code", "nl2br"])
    doc = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<style>body{font-family:Helvetica,Arial,sans-serif;font-size:11pt;padding:12px;} "
        "code,pre{font-size:9pt;} pre{background:#f5f5f5;padding:8px;}</style></head><body>"
        f"{html_body}</body></html>"
    )
    import io

    out = io.BytesIO()
    status = pisa.CreatePDF(doc, dest=out, encoding="utf-8")
    if getattr(status, "err", 0):
        return None
    return out.getvalue()


def run_preflight(question: str, paths: list[str], settings: Settings) -> tuple[str, str]:
    """Returns (human_review_markdown, trace_markdown_for_chat)."""
    q = (question or "").strip()
    if not q:
        raise ValueError("Research question is empty.")
    steps: list[str] = [
        f"Using backend: {settings.llm_provider}",
        "Building upload digest (captions / PDF excerpts)…",
    ]
    digest = build_upload_digest(paths)
    steps.append("Calling model for alignment…")
    analysis = llm_preflight_analysis(q, digest, settings)
    md = assemble_preflight_markdown(digest, analysis)
    trace = "## Preflight\n\n" + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps + ["Complete."]))
    return md, trace


def run_research(
    question: str,
    paths: list[str],
    settings: Settings,
    *,
    enable_web_search: bool,
    top_k: int,
    web_results_per_query: int,
    max_research_rounds: int,
    progress_callback=None,
) -> dict:
    """
    Run full graph; optional ``progress_callback(live_trace_md: str)`` for UI updates.
    Returns final graph state dict.
    """
    q = (question or "").strip()
    if not q:
        raise ValueError("Please enter a research question.")
    rounds = int(min(2, max(1, int(max_research_rounds))))
    graph = build_graph(settings)
    initial_state = {
        "question": q,
        "local_file_paths": list(paths),
        "enable_web_search": bool(enable_web_search),
        "top_k": int(top_k),
        "web_results_per_query": int(web_results_per_query),
        "max_research_rounds": rounds,
        "analyst_pass_count": 0,
        "trace": ["Research request accepted by the orchestrator."],
        "retrieval_log": [],
        "gap_round_log": [],
    }
    last_state: dict = initial_state
    saw_chunk = False
    if progress_callback:
        progress_callback(
            "## Research run\n\n- _Preparing graph…_\n"
        )
    for state in graph.stream(initial_state, stream_mode="values"):
        saw_chunk = True
        if isinstance(state, dict):
            last_state = state
            if progress_callback:
                progress_callback(format_live_progress(state))
    if not saw_chunk:
        last_state = graph.invoke(initial_state)
    return last_state
