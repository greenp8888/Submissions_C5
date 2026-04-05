"""
Shared research orchestration for Streamlit (no Gradio imports).

Reuses the same LangGraph pipeline and preflight as ``app.py``.
"""

from __future__ import annotations

import html
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


# Headings the LLM often uses that are not useful as the chat / file title.
_GENERIC_REPORT_HEADINGS: frozenset[str] = frozenset(
    {
        "executive summary",
        "summary",
        "introduction",
        "overview",
        "abstract",
        "report",
        "research report",
        "findings",
        "detailed findings",
        "detailed finding",
    }
)


def is_report_heading_label(text: str) -> bool:
    """True if ``text`` looks like a report section heading, not a chat name."""
    s = (text or "").strip().lower().rstrip(".")
    return s in _GENERIC_REPORT_HEADINGS


def stable_chat_title(question: str) -> str:
    """
    One-line chat label from the research question only.
    Stays the same across preview → full run → complete (never swap to a report heading).
    """
    q = (question or "").strip()
    if not q:
        return "Untitled research"
    line = q.split("\n")[0].strip()
    if len(line) > 120:
        return line[:117] + "…"
    return line


def derive_title(report_md: str, question: str) -> str:
    for line in (report_md or "").splitlines():
        line = line.strip()
        if not line.startswith("#"):
            continue
        t = line.lstrip("#").strip()
        if not t:
            continue
        norm = t.lower().rstrip(".").strip()
        if norm in _GENERIC_REPORT_HEADINGS:
            continue
        return t[:120]
    q = (question or "").strip()
    if not q:
        return "Untitled research"
    return q[:80] + ("…" if len(q) > 80 else "")


def _format_generated_utc_display(iso_ts: str) -> str:
    s = (iso_ts or "").strip()
    if not s:
        return "—"
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%d %B %Y · %H:%M UTC")
    except (ValueError, TypeError):
        return s


def build_report_cover_markdown(
    *,
    session_title: str,
    question: str,
    uploaded_paths: list[str],
    user_email: str,
    user_display_name: str,
    llm_provider: str,
    model_label: str,
    web_search_enabled: bool,
    generated_utc: str,
    planner_objective: str,
) -> str:
    """
    Structured front matter for PDF (and optional exports): session context before the narrative.
    """
    names = [Path(p).name for p in (uploaded_paths or []) if str(p).strip()]
    docs_block = "\n".join(f"- {n}" for n in names) if names else "- _(none — web and indexed sources only)_"
    who = (user_display_name or "").strip() or "—"
    email = (user_email or "").strip() or "—"
    obj = (planner_objective or "").strip()
    title_line = (session_title or "").strip() or derive_title("", question)

    return f"""# Research dossier — cover sheet

---

## Document identity

| Field | Detail |
| :--- | :--- |
| **Working title** | {title_line} |
| **Generated** | {_format_generated_utc_display(generated_utc)} |

---

## Research request

**Question**

> {(question or "").strip() or "_(not set)_"}

**Planner objective** (when available)

> {obj if obj else "_(see report body)_"}

---

## Supporting materials supplied

The following files were attached to this session for retrieval and grounding:

{docs_block}

---

## Researcher & tooling

| Attribute | Value |
| :--- | :--- |
| **Researcher** | {who} |
| **Account** | {email} |
| **LLM backend** | {llm_provider} |
| **Model** | {model_label or "—"} |
| **Open web search (Tavily)** | {"Yes" if web_search_enabled else "No"} |

---

*This cover precedes the synthesized report, gap-planning notes, and source references. Execution traces and internal logs are omitted from the PDF export.*
""".strip()


def build_report_cover_html(
    *,
    session_title: str,
    question: str,
    uploaded_paths: list[str],
    user_email: str,
    user_display_name: str,
    llm_provider: str,
    model_label: str,
    web_search_enabled: bool,
    generated_utc: str,
    planner_objective: str,
) -> str:
    """
    Microsoft Fluent–inspired cover HTML for xhtml2pdf (avoids broken pipe-table rendering).
    """
    names = [Path(p).name for p in (uploaded_paths or []) if str(p).strip()]
    who = (user_display_name or "").strip() or "—"
    email_s = (user_email or "").strip() or "—"
    obj = (planner_objective or "").strip()
    title_line = (session_title or "").strip() or derive_title("", question)
    q = (question or "").strip() or "_(not set)_"
    obj_disp = obj if obj else "—"
    gen_disp = _format_generated_utc_display(generated_utc)
    model_s = (model_label or "").strip() or "—"
    tav = "Yes" if web_search_enabled else "No"

    rows_id = [
        ("Working title", title_line),
        ("Generated", gen_disp),
    ]
    rows_tool = [
        ("Researcher", who),
        ("Account", email_s),
        ("LLM backend", llm_provider),
        ("Model", model_s),
        ("Open web search (Tavily)", tav),
    ]

    def kv_rows(rows: list[tuple[str, str]]) -> str:
        parts: list[str] = []
        for k, v in rows:
            parts.append(
                "<tr>"
                f'<td class="nm-pdf-k">{html.escape(k)}</td>'
                f'<td class="nm-pdf-v">{html.escape(v)}</td>'
                "</tr>"
            )
        return "\n".join(parts)

    if names:
        ul = '<ul class="nm-pdf-ul">' + "".join(f"<li>{html.escape(n)}</li>" for n in names) + "</ul>"
    else:
        ul = '<p class="nm-pdf-muted">No files attached (web and indexed sources only).</p>'

    return (
        '<div class="nm-pdf-cover">'
        '<table width="100%" cellspacing="0" cellpadding="0" class="nm-pdf-banner-t">'
        '<tr><td class="nm-pdf-banner">NovaMind · Deep Research</td></tr>'
        '<tr><td class="nm-pdf-banner-sub">Request for proposal · Confidential briefing</td></tr>'
        "</table>"
        '<h1 class="nm-pdf-doc-title">Research dossier</h1>'
        '<p class="nm-pdf-doc-lede">Evidence-based synthesis · Trace-free export</p>'
        '<h2 class="nm-pdf-h2">Document identity</h2>'
        f'<table width="100%" cellspacing="0" cellpadding="0" class="nm-pdf-kv">{kv_rows(rows_id)}</table>'
        '<h2 class="nm-pdf-h2">Research request</h2>'
        '<p class="nm-pdf-label">Question</p>'
        f'<div class="nm-pdf-callout">{html.escape(q)}</div>'
        '<p class="nm-pdf-label">Planner objective (when available)</p>'
        f'<div class="nm-pdf-callout">{html.escape(obj_disp)}</div>'
        '<h2 class="nm-pdf-h2">Supporting materials supplied</h2>'
        '<p class="nm-pdf-p">Files attached to this session for retrieval and grounding:</p>'
        f"{ul}"
        '<h2 class="nm-pdf-h2">Researcher &amp; tooling</h2>'
        f'<table width="100%" cellspacing="0" cellpadding="0" class="nm-pdf-kv">{kv_rows(rows_tool)}</table>'
        '<p class="nm-pdf-footnote">This cover precedes the synthesized report, gap-planning notes, and source '
        "references. Execution traces and internal orchestration logs are omitted from this PDF.</p>"
        "</div>"
        '<div class="nm-pdf-page-break"></div>'
    )


def build_pdf_body_markdown(
    *,
    report_md: str,
    gaps_md: str,
    contradictions_md: str,
    sources_detail_md: str,
) -> str:
    """
    PDF body only (after HTML cover): report, gaps, contradictions, sources.
    Does **not** include orchestration traces.
    """
    chunks: list[str] = []
    r = (report_md or "").strip()
    chunks.append(r if r else "_No report was generated._")
    g = (gaps_md or "").strip()
    if g:
        chunks.append("\n\n---\n\n## Gap planner & follow-up analysis\n\n")
        chunks.append(g)
    cc = (contradictions_md or "").strip()
    if cc:
        chunks.append("\n\n---\n\n## Contradictions & caveats\n\n")
        chunks.append(cc)
    s = (sources_detail_md or "").strip()
    if s:
        chunks.append("\n\n---\n\n## Resource references & detailed extracts\n\n")
        chunks.append(s)
    return "\n".join(chunks).strip()


def slug_filename_base(title: str, max_len: int = 48) -> str:
    s = re.sub(r"[^\w\s-]", "", (title or "research").lower())
    s = re.sub(r"[-\s]+", "-", s).strip("-") or "research"
    return s[:max_len]


def write_artifact_markdown(base_dir: Path, base_name: str, markdown_text: str) -> Path:
    base_dir.mkdir(parents=True, exist_ok=True)
    path = base_dir / f"{base_name}.md"
    path.write_text(markdown_text, encoding="utf-8")
    return path


# Microsoft Fluent–inspired typography and layout for xhtml2pdf (RFP-style brief).
_PDF_STYLES = """
@page { size: A4; margin: 16mm 14mm 18mm 14mm; }
body {
  font-family: "Segoe UI", "Segoe UI Web (West European)", Roboto, Helvetica, Arial, sans-serif;
  font-size: 10.5pt;
  color: #323130;
  line-height: 1.45;
  margin: 0;
  padding: 0;
}
.nm-pdf-cover { margin: 0 0 4mm 0; }
.nm-pdf-banner-t { width: 100%; margin: 0 0 12pt 0; border-collapse: collapse; }
.nm-pdf-banner {
  background-color: #0078D4;
  color: #FFFFFF;
  font-size: 13pt;
  font-weight: 600;
  padding: 11pt 14pt;
  letter-spacing: 0.02em;
}
.nm-pdf-banner-sub {
  background-color: #106EBE;
  color: #DEECF9;
  font-size: 8pt;
  padding: 5pt 14pt;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.nm-pdf-doc-title {
  color: #0078D4;
  font-size: 20pt;
  font-weight: 600;
  margin: 8pt 0 3pt 0;
  padding-bottom: 5pt;
  border-bottom: 2.5pt solid #0078D4;
}
.nm-pdf-doc-lede { color: #605E5C; font-size: 9.5pt; margin: 0 0 14pt 0; }
.nm-pdf-h2 {
  color: #201F1E;
  font-size: 11pt;
  font-weight: 600;
  margin: 14pt 0 7pt 0;
  padding: 6pt 10pt;
  border-left: 4pt solid #0078D4;
  background: #F3F2F1;
}
.nm-pdf-kv { border-collapse: collapse; width: 100%; margin: 0 0 11pt 0; }
.nm-pdf-kv td {
  border: 1px solid #C8C6C4;
  padding: 9pt 11pt;
  vertical-align: top;
}
.nm-pdf-k {
  width: 30%;
  background-color: #F3F2F1;
  font-weight: 600;
  color: #323130;
}
.nm-pdf-v {
  color: #201F1E;
  word-wrap: break-word;
  overflow-wrap: break-word;
}
.nm-pdf-label {
  font-size: 8pt;
  font-weight: 600;
  color: #605E5C;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 9pt 0 3pt 0;
}
.nm-pdf-callout {
  background: #FAF9F8;
  border: 1px solid #EDEBE9;
  border-left: 4pt solid #0078D4;
  padding: 9pt 11pt;
  color: #201F1E;
  margin: 0 0 7pt 0;
}
.nm-pdf-p { margin: 3pt 0 7pt 0; color: #323130; }
.nm-pdf-ul { margin: 5pt 0 10pt 20pt; color: #201F1E; padding: 0; }
.nm-pdf-ul li { margin: 4pt 0; }
.nm-pdf-muted { color: #605E5C; font-style: italic; margin: 6pt 0; }
.nm-pdf-footnote {
  font-size: 8pt;
  color: #605E5C;
  margin-top: 12pt;
  padding-top: 9pt;
  border-top: 1px solid #EDEBE9;
}
.nm-pdf-page-break { page-break-after: always; height: 1px; margin: 0; padding: 0; font-size: 0; line-height: 0; }
.nm-pdf-body { margin: 0; padding: 0; }
.nm-pdf-body h1 { font-size: 15pt; color: #0078D4; margin: 12pt 0 6pt 0; font-weight: 600; }
.nm-pdf-body h2 {
  font-size: 12pt;
  color: #201F1E;
  margin: 11pt 0 5pt 0;
  padding-bottom: 3pt;
  border-bottom: 1px solid #EDEBE9;
  font-weight: 600;
}
.nm-pdf-body h3 { font-size: 10.5pt; color: #323130; margin: 9pt 0 4pt 0; font-weight: 600; }
.nm-pdf-body p { margin: 5pt 0; }
.nm-pdf-body table { border-collapse: collapse; width: 100%; margin: 8pt 0; }
.nm-pdf-body th, .nm-pdf-body td {
  border: 1px solid #C8C6C4;
  padding: 5pt 7pt;
  vertical-align: top;
}
.nm-pdf-body th { background: #F3F2F1; font-weight: 600; color: #323130; }
.nm-pdf-body blockquote {
  border-left: 3pt solid #0078D4;
  margin: 7pt 0 7pt 6pt;
  padding-left: 9pt;
  color: #605E5C;
}
.nm-pdf-body code { font-size: 9pt; background: #F3F2F1; padding: 1pt 3pt; }
.nm-pdf-body pre {
  background: #F3F2F1;
  border: 1px solid #EDEBE9;
  padding: 7pt;
  font-size: 8.5pt;
  white-space: pre-wrap;
  word-wrap: break-word;
}
.nm-pdf-body hr { border: none; border-top: 1px solid #C8C6C4; margin: 12pt 0; }
.nm-pdf-body ul, .nm-pdf-body ol { margin: 5pt 0 5pt 18pt; }
"""


def markdown_to_pdf_bytes(md_text: str, *, cover_html: str | None = None) -> bytes | None:
    """Return PDF bytes, or None if optional deps are missing.

    Optional ``cover_html`` is prepended (Fluent-styled cover); body ``md_text`` is rendered as Markdown.
    """
    try:
        import markdown as md_lib
        from xhtml2pdf import pisa
    except ImportError:
        return None
    import io

    body_html = md_lib.markdown(md_text or "", extensions=["tables", "fenced_code", "nl2br"])
    inner = (cover_html or "") + f'<div class="nm-pdf-body">{body_html}</div>'
    doc = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'/>"
        f"<style>{_PDF_STYLES}</style></head><body>{inner}</body></html>"
    )
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
