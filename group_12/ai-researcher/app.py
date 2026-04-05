
from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import gradio as gr
import pandas as pd

from deep_researcher.config import ANTHROPIC_BUDGET_MODELS, LLM_PROVIDER_ANTHROPIC, LLM_PROVIDER_OPENROUTER, Settings
from deep_researcher.graph import build_graph, normalize_excerpt_whitespace
from deep_researcher.preflight import assemble_preflight_markdown, build_upload_digest, llm_preflight_analysis
from deep_researcher.retrieval import _classify_local_paths

# Common OpenRouter model ids (custom values allowed in the dropdown).
OPENROUTER_MODEL_PRESETS: list[str] = [
    "openai/gpt-4o-mini",
    "openai/gpt-4o",
    "openai/gpt-4-turbo",
    "anthropic/claude-3.5-haiku",
    "google/gemini-flash-1.5",
    "google/gemini-pro-1.5",
    "meta-llama/llama-3.3-70b-instruct",
    "mistralai/mistral-small-24b-instruct-2501",
    "deepseek/deepseek-chat",
]

# Tab order (left to right): Human review → Report → Sources → Trace & gaps
TAB_HUMAN, TAB_REPORT, TAB_SOURCES, TAB_TRACE = 0, 1, 2, 3

REVIEW_BUTTON_LABEL = "Review uploads & question"
RUN_RESEARCH_BUTTON_LABEL = "Run full research"

_APP_DIR = Path(__file__).resolve().parent
LOGO_PATH = _APP_DIR / "assets" / "novamind-logo.png"

# NovaMind design system — see docs/images/novamind_design_system.md
# Avoid @import of Google Fonts here: it blocks first paint and can make the UI feel frozen on load.
NOVAMIND_CSS = """
:root {
  --nm-bg-deep: #080a0f;
  --nm-bg: #0c0e14;
  --nm-surface: #12161f;
  --nm-elevated: #181e2a;
  --nm-border: rgba(100, 180, 255, 0.14);
  --nm-text: #e8edf7;
  --nm-muted: #8b9cb3;
  --nm-accent: #22d3ee;
  --nm-accent-dim: rgba(34, 211, 238, 0.12);
  --nm-violet: #a78bfa;
  --nm-r: 14px;
  --nm-rs: 10px;
}

.gradio-container {
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
  background: var(--nm-bg-deep) !important;
  color: var(--nm-text) !important;
}

.nm-wrap { max-width: 1320px; margin: 0 auto; padding: 0.35rem 0 2.5rem; }

.nm-hero {
  background: linear-gradient(165deg, var(--nm-surface) 0%, rgba(24, 30, 42, 0.55) 100%);
  border: 1px solid var(--nm-border);
  border-radius: var(--nm-r);
  padding: 1.35rem 1.5rem 1.2rem;
  margin-bottom: 1.2rem;
}
.nm-hero-top {
  display: flex !important; flex-wrap: wrap; align-items: flex-start; justify-content: space-between;
  gap: 1.15rem; margin-bottom: 0.85rem;
}
.nm-hero-left { display: flex !important; gap: 1rem; align-items: flex-start; flex: 1 1 280px; min-width: 0; }
.nm-brand-logo-wrap { flex-shrink: 0; }
.nm-brand-logo-wrap img, .nm-brand-logo-wrap .image-container img {
  width: 64px !important; height: 64px !important; object-fit: contain !important;
  border-radius: 14px !important; background: rgba(255,255,255,0.04) !important;
}
.nm-connect-compact {
  flex: 0 0 auto !important; align-self: flex-start !important;
  display: flex !important; flex-direction: row !important; align-items: center !important;
  justify-content: flex-end !important; gap: 0.45rem !important;
  background: var(--nm-elevated); border: 1px solid var(--nm-border);
  border-radius: 999px; padding: 0.28rem 0.5rem 0.28rem 0.85rem;
}
.nm-connect-chip-wrap { flex: 1 1 auto !important; min-width: 0 !important; margin: 0 !important; }
.nm-connect-chip-wrap .markdown, .nm-connect-chip-wrap p { margin: 0 !important; }
.nm-connect-chip { margin: 0 !important; font-size: 0.88rem !important; font-weight: 500 !important; color: var(--nm-text) !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: min(42vw, 22rem); }
.nm-connect-chip code { font-size: 0.84rem !important; color: var(--nm-accent) !important; background: rgba(0,0,0,0.25) !important; padding: 0.12rem 0.4rem !important; border-radius: 6px !important; border: 1px solid var(--nm-border) !important; }
.nm-icon-btn {
  min-width: 2.25rem !important; max-width: 2.25rem !important; height: 2.25rem !important; padding: 0 !important;
  font-size: 1.15rem !important; line-height: 1 !important; border-radius: 999px !important;
  background: transparent !important; border: 1px solid var(--nm-border) !important; color: var(--nm-text) !important;
}
.nm-icon-btn:hover { border-color: var(--nm-accent) !important; background: var(--nm-accent-dim) !important; }
.nm-connect-popover {
  position: fixed !important; top: 4.5rem !important; right: max(1rem, 2vw) !important;
  width: min(440px, calc(100vw - 2rem)) !important; max-height: min(640px, 85vh) !important;
  overflow-y: auto !important; z-index: 10000 !important;
  background: var(--nm-surface) !important; border: 1px solid var(--nm-border) !important;
  border-radius: var(--nm-r) !important; box-shadow: 0 28px 90px rgba(0,0,0,0.75) !important;
  padding: 1rem 1.15rem 1.1rem !important;
}
.nm-connect-popover .markdown, .nm-connect-popover p, .nm-connect-popover label span { color: var(--nm-text) !important; }

.nm-brand-row { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.25rem; }
/* Solid wordmark — gradient clip often disappears in some browsers / themes */
.nm-wordmark {
  font-size: 1.48rem; font-weight: 700; letter-spacing: -0.03em; color: #f1f5f9 !important;
  text-shadow: 0 0 24px rgba(34, 211, 238, 0.15);
}
.nm-logo-gradient {
  font-size: 1.48rem; font-weight: 700; letter-spacing: -0.03em;
  background: linear-gradient(135deg, #5eead4, #a78bfa);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.nm-hero-more {
  margin-top: 0.35rem !important;
  border: 1px solid var(--nm-border) !important;
  border-radius: var(--nm-rs) !important;
  background: rgba(0,0,0,0.15) !important;
  overflow: hidden;
}
.nm-hero-more details { border: none !important; background: transparent !important; padding: 0 !important; }
.nm-hero-more summary { cursor: pointer; font-size: 0.84rem !important; color: var(--nm-muted) !important; list-style: none; }
.nm-hero-more summary::-webkit-details-marker { display: none; }
.nm-hero-more .prose, .nm-hero-more .markdown {
  margin-top: 0.5rem !important; font-size: 0.88rem !important; line-height: 1.55 !important; color: var(--nm-muted) !important;
}
.nm-hero-more strong { color: var(--nm-text) !important; }
.nm-hero-more code { color: var(--nm-accent) !important; }
.nm-badge {
  font-size: 0.62rem; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--nm-accent); border: 1px solid var(--nm-border); padding: 0.22rem 0.6rem; border-radius: 999px;
  background: var(--nm-accent-dim);
}
.nm-tagline { font-size: 1.02rem; font-weight: 500; color: var(--nm-muted); margin: 0.45rem 0 0.35rem 0; }
.nm-connect-hint { font-size: 0.8rem; color: var(--nm-muted); margin: 0.4rem 0 0 0; line-height: 1.45; }

.nm-workspace { gap: 1.25rem !important; align-items: flex-start !important; }
.nm-sidebar { display: flex; flex-direction: column; gap: 0.95rem !important; }
.nm-main { display: flex; flex-direction: column; gap: 0.95rem !important; min-width: 0; }

.nm-card {
  background: var(--nm-surface) !important;
  border: 1px solid var(--nm-border) !important;
  border-radius: var(--nm-r) !important;
  padding: 0.95rem 1.05rem !important;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
}
.nm-card h1, .nm-card h2, .nm-card h3 {
  font-size: 0.66rem !important; font-weight: 600 !important; letter-spacing: 0.11em !important;
  text-transform: uppercase !important; color: var(--nm-muted) !important;
  margin: 0 0 0.75rem 0 !important; border: none !important;
}

.nm-status-strip {
  background: var(--nm-elevated) !important;
  border: 1px solid var(--nm-border) !important;
  border-radius: var(--nm-rs) !important;
  padding: 0.65rem 0.95rem !important;
  font-size: 0.88rem;
  color: var(--nm-text) !important;
}
.nm-status-strip .markdown, .nm-status-strip p, .nm-status-strip li, .nm-status-strip strong {
  color: var(--nm-text) !important;
}
.nm-status-strip em { color: var(--nm-muted) !important; }

/* Gradio markdown / prose: force readable foreground on dark shell */
.gradio-container .markdown-body, .gradio-container .prose, .gradio-container .prose p,
.gradio-container .prose li, .gradio-container .prose strong { color: var(--nm-text) !important; }
.gradio-container .prose em, .gradio-container .markdown em { color: var(--nm-muted) !important; }
.gradio-container .prose code { color: var(--nm-accent) !important; background: var(--nm-elevated) !important; }

.nm-file-hint .markdown, .nm-file-hint p { color: var(--nm-muted) !important; }
.nm-file-hint strong { color: var(--nm-text) !important; }

.nm-tabs-shell {
  background: var(--nm-surface) !important;
  border: 1px solid var(--nm-border) !important;
  border-radius: var(--nm-r) !important;
  padding: 0.5rem 0.65rem 1rem !important;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
}

.gradio-tabs { margin-top: 0 !important; }
.gradio-tab-nav { gap: 0.35rem !important; border-bottom: 1px solid var(--nm-border) !important; padding-bottom: 0.45rem !important; margin-bottom: 0.65rem !important; flex-wrap: wrap !important; }
/* Gradio 5/6: tab labels must stay high-contrast on near-black backgrounds */
.gradio-tab-nav button,
.nm-tabs-shell [role="tab"] {
  color: #d8e3f0 !important;
  border: none !important; background: transparent !important;
  font-weight: 500 !important; font-size: 0.86rem !important; padding: 0.45rem 0.85rem !important; border-radius: 8px !important;
  opacity: 1 !important;
}
.gradio-tab-nav button.selected,
.nm-tabs-shell [role="tab"][aria-selected="true"] {
  color: #f8fafc !important;
  background: var(--nm-accent-dim) !important;
  box-shadow: inset 0 0 0 1px rgba(34, 211, 238, 0.45) !important;
}
/* While a job runs, Gradio may add .pending or disable tab controls — avoid unreadable dimming.
   Do NOT use :has() on .gradio-container — it forces constant descendant scans and can freeze the tab. */
.gradio-container.pending .gradio-tab-nav button:not(.selected),
.gradio-container.pending .nm-tabs-shell [role="tab"]:not([aria-selected="true"]),
.gradio-tab-nav button:disabled,
.nm-tabs-shell [role="tab"][aria-disabled="true"] {
  color: #e2e8f0 !important; opacity: 0.98 !important;
}

/* Report / markdown: model output often uses ## headers — Gradio prose defaults can be near-black */
.nm-main .prose h1, .nm-main .prose h2, .nm-main .prose h3, .nm-main .prose h4, .nm-main .prose h5, .nm-main .prose h6,
.report-citations-prose .prose h1, .report-citations-prose .prose h2, .report-citations-prose .prose h3,
.report-citations-prose .prose h4, .report-citations-prose .prose h5, .report-citations-prose .prose h6,
.nm-main .markdown h1, .nm-main .markdown h2, .nm-main .markdown h3, .nm-main .markdown h4,
.report-citations-prose h1, .report-citations-prose h2, .report-citations-prose h3 {
  color: #eef2f8 !important;
  font-weight: 600 !important;
}
.nm-main .prose strong, .report-citations-prose .prose strong { color: #f1f5f9 !important; }
.nm-main .prose hr, .report-citations-prose .prose hr { border-color: rgba(100, 180, 255, 0.25) !important; }
.nm-main .prose blockquote, .report-citations-prose .prose blockquote {
  color: #c5d2e3 !important; border-left-color: var(--nm-accent) !important;
}
.nm-main .prose li::marker, .report-citations-prose .prose li::marker { color: var(--nm-accent) !important; }

.gradio-container textarea, .gradio-container input[type="text"], .gradio-container input[type="password"] {
  background: var(--nm-elevated) !important; border: 1px solid var(--nm-border) !important;
  color: var(--nm-text) !important; border-radius: var(--nm-rs) !important;
}
.gradio-container textarea:focus, .gradio-container input:focus { border-color: var(--nm-accent) !important; box-shadow: 0 0 0 2px var(--nm-accent-dim) !important; }

.gradio-container label span, .gradio-container .label-wrap span { color: var(--nm-muted) !important; font-size: 0.82rem !important; }

.gradio-container button.primary {
  background: linear-gradient(135deg, #06b6d4, #6366f1) !important; color: #041014 !important;
  font-weight: 600 !important; border: none !important; border-radius: var(--nm-rs) !important;
}
.gradio-container button.secondary {
  background: transparent !important; color: var(--nm-text) !important;
  border: 1px solid var(--nm-border) !important; border-radius: var(--nm-rs) !important;
}

.gradio-container .slider_input_container input { background: var(--nm-elevated) !important; }

#nm-trace-panel, #nm-gaps-panel {
  font-family: ui-monospace, "Cascadia Code", "SF Mono", Menlo, Consolas, monospace !important;
  font-size: 0.82rem !important; line-height: 1.5 !important;
  color: var(--nm-text) !important;
}
#nm-trace-panel em, #nm-gaps-panel em { color: var(--nm-muted) !important; }

.report-citations-prose { line-height: 1.65; max-width: 100%; color: var(--nm-text) !important; }
.report-citations-prose .markdown, .report-citations-prose .prose, .report-citations-prose p { color: var(--nm-text) !important; }
.report-citations-prose a {
  display: inline-flex; align-items: center; background: var(--nm-elevated);
  padding: 0.15rem 0.55rem 0.18rem; border-radius: 999px; font-size: 0.78rem; font-weight: 500;
  color: var(--nm-accent) !important; text-decoration: none !important;
  border: 1px solid rgba(34, 211, 238, 0.35); margin: 0 0.12rem; vertical-align: 0.08em; line-height: 1.25;
}
.report-citations-prose a:hover { border-color: var(--nm-accent); background: var(--nm-accent-dim); }

.gradio-container .pending { opacity: 0.9; }
"""


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
    """Readable pipeline status for the Trace tab while the graph runs."""
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
            lines.append(f"- {item[:500]}{'…' if len(str(item)) > 500 else ''}")
    return "\n".join(lines)


def create_downloadable_report(markdown_text: str) -> str:
    output_dir = Path(tempfile.mkdtemp(prefix="deep_research_report_"))
    output_path = output_dir / "research_report.md"
    output_path.write_text(markdown_text, encoding="utf-8")
    return str(output_path)


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
            "_No gap-planning output yet. Use **Max analyst passes** = 2 to enable a follow-up "
            "retrieval wave after the first critical analysis._"
        )
    return "\n\n---\n\n".join(logs)


def format_objective_markdown(objective: str | None) -> str:
    o = (objective or "").strip()
    if not o:
        return "_The planner did not return a separate objective line (check trace)._"
    return f"**Planner objective:** {o}"


def on_files_updated(files):
    """Summarize staged uploads after File changes (keep sync + single UI update — no streaming)."""
    paths = collect_upload_paths(files)
    if not paths:
        return "_No files attached. Upload PDFs, images, or audio when you are ready._"
    # Gradio may emit change before each temp path is fully written (common on large uploads).
    for p in paths:
        try:
            if not Path(p).is_file():
                return (
                    "_**Upload in progress.**_ The browser is still transferring this file; the summary will "
                    "refresh when the server has the full copy. Very large files can take a minute._"
                )
        except OSError:
            return (
                "_**Upload in progress.**_ Waiting for the file to become available on the server._"
            )
    pdfs, images, audios, skipped = _classify_local_paths(paths)
    names = [Path(p).name for p in paths[:12]]
    more = " …" if len(paths) > 12 else ""
    lines = [
        f"**✓ {len(paths)} file(s) ready** on the server",
        "",
        f"- **PDF:** {len(pdfs)} · **Image:** {len(images)} · **Audio:** {len(audios)} · **Unclassified:** {len(skipped)}",
        "",
        f"_Files: {', '.join(names)}{more}_",
    ]
    if skipped:
        lines.append(
            "\n_Unclassified (could not detect type from extension or file header): "
            f"{len(skipped)} — check the file or try another format._"
        )
    return "\n".join(lines)


def collect_upload_paths(files) -> list[str]:
    """Normalize Gradio file upload(s) to local path strings."""

    def _one(f) -> str | None:
        if f is None:
            return None
        if isinstance(f, str) and f.strip():
            return f.strip()
        if isinstance(f, Path):
            s = str(f)
            return s if s.strip() else None
        if hasattr(f, "__fspath__"):
            s = str(f)
            return s if s.strip() else None
        if isinstance(f, dict):
            for key in ("path", "name", "file_path"):
                v = f.get(key)
                if isinstance(v, str) and v.strip():
                    return v.strip()
            return None
        for attr in ("name", "path", "file_path"):
            v = getattr(f, attr, None)
            if isinstance(v, str) and v.strip():
                return v.strip()
        return None

    out: list[str] = []
    if not files:
        return out
    iterable = files if isinstance(files, list) else [files]
    for f in iterable:
        p = _one(f)
        if p:
            out.append(p)
    return out


def _settings_from_ui(
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


def _toggle_provider_panels(provider: str):
    use_openrouter = (provider or "").strip() == LLM_PROVIDER_OPENROUTER
    return gr.update(visible=use_openrouter), gr.update(visible=not use_openrouter)


def _llm_backend_label(settings: Settings) -> str:
    if settings.llm_provider == LLM_PROVIDER_ANTHROPIC:
        return f"Anthropic **{settings.anthropic_model}** (Haiku / budget)"
    return f"OpenRouter **`{settings.openrouter_model}`**"


def _preflight_trace_block(lines: list[str]) -> str:
    body = "\n".join(f"{i + 1}. {line}" for i, line in enumerate(lines))
    return f"## Preflight progress\n\n{body}"


def run_preflight_review(
    question: str,
    files,
    llm_provider: str,
    openrouter_key: str,
    openrouter_model: str,
    anthropic_key: str,
    anthropic_model: str,
):
    """Stream preflight steps; switch to Trace, then finish in Human review tab."""
    q = (question or "").strip()
    if not q:
        raise gr.Error("Please enter a research question.")

    try:
        settings = _settings_from_ui(
            llm_provider, openrouter_key, openrouter_model, anthropic_key, anthropic_model
        )
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc

    steps: list[str] = []
    _rb_busy = gr.update(interactive=False, value="⏳ Review in progress…")
    _rb_idle = gr.update(interactive=True, value=REVIEW_BUTTON_LABEL)

    steps.append(f"Using {_llm_backend_label(settings)} for alignment check.")
    steps.append("Validating question and classifying uploads…")
    yield (
        gr.skip(),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(selected=TAB_TRACE),
        _preflight_trace_block(steps),
        _rb_busy,
    )

    paths = collect_upload_paths(files)
    steps.append(f"Found {len(paths)} upload path(s); building digest (captions / PDF excerpts)…")
    yield (
        gr.skip(),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(selected=TAB_TRACE),
        _preflight_trace_block(steps),
        _rb_busy,
    )

    try:
        digest = build_upload_digest(paths)
        steps.append("Digest ready — calling the model for upload ↔ question alignment…")
        yield (
            gr.skip(),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(selected=TAB_TRACE),
            _preflight_trace_block(steps),
            _rb_busy,
        )
        analysis = llm_preflight_analysis(q, digest, settings)
        md = assemble_preflight_markdown(digest, analysis)
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc
    except Exception as exc:
        raise gr.Error(f"Preflight failed: {exc!s}") from exc

    steps.append("Preflight complete — open **Human review** to read the summary.")
    yield (
        md,
        gr.update(visible=True, interactive=True, value=RUN_RESEARCH_BUTTON_LABEL),
        gr.update(visible=True),
        gr.update(selected=TAB_HUMAN),
        _preflight_trace_block(steps),
        _rb_idle,
    )


def cancel_preflight_review():
    """User declined to continue — stay on the same page and reset the review strip."""
    return (
        "_You chose **not** to run research. Change your **research question** or **uploads**, then click "
        "**Review uploads & question** again._",
        gr.update(visible=False),
        gr.update(visible=False),
    )


def finalize_research_outputs(result: dict) -> tuple:
    report = result.get("final_report", "No report was generated.")
    detailed_md = (result.get("detailed_extracts_markdown") or "").strip()
    evidence_df = evidence_to_dataframe(result.get("evidence", []))
    trace_md = trace_to_markdown(
        result.get("trace", []),
        result.get("retrieval_log"),
    )
    contradictions = result.get("contradictions", []) or []
    contradictions_md = "\n".join(f"- {item}" for item in contradictions) or "_No explicit contradictions noted._"
    gaps_md = format_gaps_markdown(result.get("gap_round_log"))
    objective_md = format_objective_markdown(result.get("research_objective"))
    download_markdown = (
        f"{report}\n\n---\n\n## Detailed extracts\n\n{detailed_md}" if detailed_md else report
    )
    download_path = create_downloadable_report(download_markdown)
    sources_detail = detailed_md or "_No detailed extracts (nothing retrieved)._"
    return (
        report,
        gaps_md,
        objective_md,
        evidence_df,
        trace_md,
        contradictions_md,
        download_path,
        sources_detail,
    )


def run_research_after_confirm(
    question: str,
    files,
    enable_web_search: bool,
    top_k: int,
    web_results_per_query: int,
    max_research_rounds: float,
    llm_provider: str,
    openrouter_key: str,
    openrouter_model: str,
    anthropic_key: str,
    anthropic_model: str,
):
    """Run LangGraph with live trace updates; finish on Report tab."""
    q = (question or "").strip()
    if not q:
        raise gr.Error("Please enter a research question.")

    rounds = int(min(2, max(1, int(max_research_rounds))))

    try:
        settings = _settings_from_ui(
            llm_provider, openrouter_key, openrouter_model, anthropic_key, anthropic_model
        )
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc

    _run_busy = gr.update(visible=True, interactive=False, value="⏳ Running full research…")
    _run_hide = gr.update(visible=False)
    _review_busy = gr.update(interactive=False, value="⏳ Research running…")
    _review_idle = gr.update(interactive=True, value=REVIEW_BUTTON_LABEL)

    # Yield immediately so the Trace tab + trace panel update before graph compilation (can be slow).
    yield (
        gr.skip(),
        gr.skip(),
        gr.skip(),
        gr.skip(),
        (
            f"## Research run\n\n"
            f"- Backend: {_llm_backend_label(settings)}\n"
            f"- _Switching to **Trace & gaps** — preparing the LangGraph orchestrator…_\n"
        ),
        gr.skip(),
        gr.skip(),
        gr.skip(),
        _run_busy,
        _run_hide,
        gr.update(selected=TAB_TRACE),
        _review_busy,
    )

    graph = build_graph(settings)
    local_paths = collect_upload_paths(files)

    initial_state = {
        "question": q,
        "local_file_paths": local_paths,
        "enable_web_search": bool(enable_web_search),
        "top_k": int(top_k),
        "web_results_per_query": int(web_results_per_query),
        "max_research_rounds": rounds,
        "analyst_pass_count": 0,
        "trace": ["Research request accepted by the orchestrator."],
        "retrieval_log": [],
        "gap_round_log": [],
    }

    boot_trace = (
        f"## Research run\n\n"
        f"- Backend: {_llm_backend_label(settings)}\n"
        f"- _Graph ready — streaming LangGraph steps below._\n"
    )
    yield (
        gr.skip(),
        gr.skip(),
        gr.skip(),
        gr.skip(),
        boot_trace,
        gr.skip(),
        gr.skip(),
        gr.skip(),
        _run_busy,
        _run_hide,
        gr.update(selected=TAB_TRACE),
        _review_busy,
    )

    last_state: dict = initial_state
    try:
        saw_chunk = False
        for state in graph.stream(initial_state, stream_mode="values"):
            saw_chunk = True
            if isinstance(state, dict):
                last_state = state
                yield (
                    gr.skip(),
                    gr.skip(),
                    gr.skip(),
                    gr.skip(),
                    format_live_progress(state),
                    gr.skip(),
                    gr.skip(),
                    gr.skip(),
                    _run_busy,
                    _run_hide,
                    gr.update(selected=TAB_TRACE),
                    _review_busy,
                )
        if not saw_chunk:
            last_state = graph.invoke(initial_state)
    except Exception as exc:
        raise gr.Error(f"Research failed: {exc!s}") from exc

    fin = finalize_research_outputs(last_state)
    _confirm_reset = gr.update(visible=False, interactive=True, value=RUN_RESEARCH_BUTTON_LABEL)
    yield (
        *fin,
        _confirm_reset,
        _confirm_reset,
        gr.update(selected=TAB_REPORT),
        _review_idle,
    )


def _app_ready_message() -> str:
    return (
        "**Workspace ready.** Stage **Corpus**, set your **Question**, then **Review**. "
        "Model and provider are shown top-right; use **⚙** for API keys and options."
    )


def format_connect_chip(
    llm_provider: str,
    _openrouter_key: str,
    openrouter_model: str,
    _anthropic_key: str,
    anthropic_model: str,
) -> str:
    """Single-line chat-style chip: provider · model (no secrets)."""
    p = (llm_provider or "").strip()
    if p == LLM_PROVIDER_ANTHROPIC:
        prov = "Anthropic"
        model = (anthropic_model or "").strip() or ANTHROPIC_BUDGET_MODELS[0]
    else:
        prov = "OpenRouter"
        model = (openrouter_model or "").strip() or "openai/gpt-4o-mini"
    return f'<p class="nm-connect-chip"><code>{prov}</code> · <code>{model}</code></p>'


def _refresh_connect_chip(
    llm_provider: str,
    openrouter_key: str,
    openrouter_model: str,
    anthropic_key: str,
    anthropic_model: str,
) -> str:
    return format_connect_chip(
        llm_provider, openrouter_key, openrouter_model, anthropic_key, anthropic_model
    )


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="NovaMind · Deep Researcher") as demo:
        with gr.Column(elem_classes=["nm-wrap"]):
            with gr.Column(visible=False, elem_classes=["nm-connect-popover"]) as connect_popover:
                gr.Markdown("### Settings")
                gr.HTML(
                    "<p class='nm-connect-hint'>API keys stay in the browser until you run Review or Research. "
                    "Leave empty to use the server <code>.env</code>.</p>"
                )
                llm_provider = gr.Radio(
                    label="LLM backend",
                    choices=[
                        ("OpenRouter (multi-model gateway)", LLM_PROVIDER_OPENROUTER),
                        ("Anthropic — Claude Haiku (budget)", LLM_PROVIDER_ANTHROPIC),
                    ],
                    value=LLM_PROVIDER_OPENROUTER,
                )
                with gr.Column(visible=True) as openrouter_panel:
                    openrouter_key = gr.Textbox(
                        label="OpenRouter API key",
                        type="password",
                        placeholder="sk-or-… → OPENROUTER_API_KEY",
                    )
                    openrouter_model = gr.Dropdown(
                        label="Model",
                        choices=OPENROUTER_MODEL_PRESETS,
                        value="openai/gpt-4o-mini",
                        allow_custom_value=True,
                    )
                with gr.Column(visible=False) as anthropic_panel:
                    anthropic_key = gr.Textbox(
                        label="Anthropic API key",
                        type="password",
                        placeholder="sk-ant-… → ANTHROPIC_API_KEY",
                    )
                    anthropic_model = gr.Dropdown(
                        label="Haiku model",
                        choices=list(ANTHROPIC_BUDGET_MODELS),
                        value=ANTHROPIC_BUDGET_MODELS[0],
                    )
                connect_done_btn = gr.Button("Done", variant="primary")

            with gr.Column(elem_classes=["nm-hero"]):
                with gr.Row(elem_classes=["nm-hero-top"]):
                    with gr.Row(elem_classes=["nm-hero-left"]):
                        if LOGO_PATH.is_file():
                            gr.Image(
                                value=str(LOGO_PATH),
                                label="",
                                show_label=False,
                                height=72,
                                width=72,
                                interactive=False,
                                container=False,
                                elem_classes=["nm-brand-logo-wrap"],
                            )
                        else:
                            gr.HTML(
                                "<div style='width:72px;height:72px;border-radius:14px;"
                                "background:#181e2a;border:1px solid rgba(100,180,255,0.2);'></div>"
                            )
                        with gr.Column(scale=4):
                            gr.HTML(
                                """
<div class="nm-brand-row">
  <span class="nm-wordmark" aria-label="NovaMind">NovaMind</span>
  <span class="nm-badge">Deep Research</span>
</div>
<p class="nm-tagline">Synthesize evidence. Trace every step.</p>
"""
                            )
                            _HERO_MORE = (
                                "Local-first LangGraph pipeline: human review of uploads, multi-source retrieval "
                                "(files, Wikipedia, arXiv, Tavily), critical analysis, and a citation-forward report. "
                                "The **Trace** tab streams orchestration as it runs. Use the **⚙** control "
                                "(top right) for provider, model, and API keys — or set `LLM_PROVIDER` and keys "
                                "in `.env` on the server."
                            )
                            with gr.Accordion("Show more", open=False, elem_classes=["nm-hero-more"]):
                                gr.Markdown(_HERO_MORE)

                    with gr.Row(elem_classes=["nm-connect-compact"]):
                        connect_chip_md = gr.Markdown(
                            value=format_connect_chip(
                                LLM_PROVIDER_OPENROUTER,
                                "",
                                "openai/gpt-4o-mini",
                                "",
                                ANTHROPIC_BUDGET_MODELS[0],
                            ),
                            elem_classes=["nm-connect-chip-wrap"],
                        )
                        settings_btn = gr.Button(
                            "⚙",
                            variant="secondary",
                            elem_classes=["nm-icon-btn"],
                            min_width=44,
                            scale=0,
                        )

            with gr.Row(elem_classes=["nm-workspace"]):
                with gr.Column(scale=5, elem_classes=["nm-sidebar"]):
                    with gr.Column(elem_classes=["nm-card"]):
                        gr.Markdown("### Corpus")
                        files = gr.File(
                            label="Uploads",
                            file_count="multiple",
                            file_types=[
                                ".pdf",
                                ".png",
                                ".jpg",
                                ".jpeg",
                                ".webp",
                                ".gif",
                                ".bmp",
                                ".tif",
                                ".tiff",
                                ".mp3",
                                ".wav",
                                ".m4a",
                                ".flac",
                                ".ogg",
                                ".webm",
                            ],
                            type="filepath",
                        )
                        file_upload_status = gr.Markdown(
                            value=(
                                "_No files staged. On upload, NovaMind validates types (PDF / image / audio). "
                                "Large files (10MB+) may take time in the **browser** before the summary appears._"
                            ),
                            elem_classes=["nm-file-hint"],
                        )

                    with gr.Column(elem_classes=["nm-card"]):
                        gr.Markdown("### Question")
                        question = gr.Textbox(
                            label="Research question",
                            lines=5,
                            placeholder="What should the agents investigate? Mention constraints, time range, or required sources.",
                        )

                    with gr.Column(elem_classes=["nm-card"]):
                        gr.Markdown("### Retrieval")
                        enable_web_search = gr.Checkbox(
                            label="Tavily web search",
                            value=True,
                        )
                        with gr.Row():
                            top_k = gr.Slider(
                                label="Top-K (FAISS)",
                                minimum=2,
                                maximum=8,
                                step=1,
                                value=4,
                            )
                            web_results_per_query = gr.Slider(
                                label="Web hits / query",
                                minimum=1,
                                maximum=5,
                                step=1,
                                value=3,
                            )
                        max_research_rounds = gr.Slider(
                            label="Analyst passes (2 = gap planner + follow-up wave)",
                            minimum=1,
                            maximum=2,
                            step=1,
                            value=1,
                        )

                    with gr.Column(elem_classes=["nm-card"]):
                        gr.Markdown("### Run")
                        review_button = gr.Button(REVIEW_BUTTON_LABEL, variant="primary")
                        with gr.Row():
                            confirm_yes = gr.Button(
                                RUN_RESEARCH_BUTTON_LABEL, variant="primary", visible=False
                            )
                            confirm_no = gr.Button("Cancel", variant="secondary", visible=False)

                with gr.Column(scale=8, elem_classes=["nm-main"]):
                    with gr.Column(elem_classes=["nm-status-strip"]):
                        ui_ready_md = gr.Markdown(value=_app_ready_message())
                        planner_objective = gr.Markdown(
                            value="_Planner objective appears after a research run._"
                        )

                    with gr.Column(elem_classes=["nm-tabs-shell"]):
                        with gr.Tabs(selected=TAB_HUMAN) as main_tabs:
                            with gr.Tab("Human review"):
                                human_review_md = gr.Markdown(
                                    value=(
                                        "_Run **Review uploads & question** to see captions, PDF excerpts, "
                                        "and alignment with your goal. Then confirm **Run full research**._"
                                    )
                                )
                            with gr.Tab("Report"):
                                with gr.Column(elem_classes=["report-citations-prose"]):
                                    gr.Markdown(
                                        "_Narrative first, with inline source chips. References and appendix follow._"
                                    )
                                    report = gr.Markdown()
                                    gr.Markdown("**Contradictions**")
                                    contradictions = gr.Markdown()
                                    download_report = gr.File(label="Download report (.md)")
                            with gr.Tab("Sources"):
                                gr.Markdown("_Evidence catalog (truncated excerpts). Detailed extracts below._")
                                evidence_table = gr.Dataframe(label="Evidence", interactive=False)
                                sources_detail_md = gr.Markdown(value="_No extracts yet._")
                            with gr.Tab("Trace & gaps"):
                                gaps_panel = gr.Markdown(
                                    elem_id="nm-gaps-panel",
                                    value="_Gap planner output when analyst passes = 2._",
                                )
                                trace_md = gr.Markdown(elem_id="nm-trace-panel", value="_Pipeline trace will stream here._")

        llm_inputs = [
            llm_provider,
            openrouter_key,
            openrouter_model,
            anthropic_key,
            anthropic_model,
        ]

        def _on_llm_provider_change(
            p: str, ok: str, om: str, ak: str, am: str
        ) -> tuple:
            u1, u2 = _toggle_provider_panels(p)
            return u1, u2, format_connect_chip(p, ok, om, ak, am)

        llm_provider.change(
            fn=_on_llm_provider_change,
            inputs=llm_inputs,
            outputs=[openrouter_panel, anthropic_panel, connect_chip_md],
            show_progress=False,
        )
        for _conn_comp in (openrouter_key, openrouter_model, anthropic_key, anthropic_model):
            _conn_comp.change(
                fn=_refresh_connect_chip,
                inputs=llm_inputs,
                outputs=[connect_chip_md],
                show_progress=False,
            )

        settings_btn.click(
            lambda: gr.update(visible=True),
            inputs=[],
            outputs=[connect_popover],
            show_progress=False,
        )
        connect_done_btn.click(
            lambda: gr.update(visible=False),
            inputs=[],
            outputs=[connect_popover],
            show_progress=False,
        )

        files.change(
            fn=on_files_updated,
            inputs=[files],
            outputs=[file_upload_status],
            # Avoid full-screen progress overlay during uploads (blocks the whole UI while Gradio streams).
            show_progress=False,
        )

        review_button.click(
            fn=run_preflight_review,
            inputs=[question, files, *llm_inputs],
            outputs=[human_review_md, confirm_yes, confirm_no, main_tabs, trace_md, review_button],
            show_progress="minimal",
        )

        confirm_no.click(
            fn=cancel_preflight_review,
            inputs=[],
            outputs=[human_review_md, confirm_yes, confirm_no],
            show_progress=False,
        )

        confirm_yes.click(
            fn=run_research_after_confirm,
            inputs=[
                question,
                files,
                enable_web_search,
                top_k,
                web_results_per_query,
                max_research_rounds,
                *llm_inputs,
            ],
            outputs=[
                report,
                gaps_panel,
                planner_objective,
                evidence_table,
                trace_md,
                contradictions,
                download_report,
                sources_detail_md,
                confirm_yes,
                confirm_no,
                main_tabs,
                review_button,
            ],
            show_progress="minimal",
        )

    demo.queue(default_concurrency_limit=4)
    return demo


if __name__ == "__main__":
    import os

    server_name = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")
    server_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))

    app = build_ui()
    app.launch(
        server_name=server_name,
        server_port=server_port,
        share=True,
        css=NOVAMIND_CSS,
    )
