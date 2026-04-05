
from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import gradio as gr
import pandas as pd

from deep_researcher.config import ANTHROPIC_BUDGET_MODELS, LLM_PROVIDER_ANTHROPIC, LLM_PROVIDER_OPENROUTER, Settings
from deep_researcher.graph import build_graph, normalize_excerpt_whitespace
from deep_researcher.preflight import human_preflight_markdown
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

# ChatGPT-style rounded chips for inline markdown links in the report tab (Gradio renders `<a href>`).
REPORT_CITATION_CSS = """
.report-citations-prose a {
    display: inline-flex;
    align-items: center;
    background: linear-gradient(180deg, #f6f6f7 0%, #ececef 100%);
    padding: 0.15rem 0.55rem 0.18rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 500;
    color: #374151 !important;
    text-decoration: none !important;
    border: 1px solid #e5e7eb;
    margin: 0 0.12rem;
    vertical-align: 0.08em;
    line-height: 1.25;
    box-shadow: 0 1px 0 rgba(0,0,0,0.05);
}
.report-citations-prose a:hover {
    background: linear-gradient(180deg, #eeeef1 0%, #e2e2e8 100%);
    border-color: #d1d5db;
}
.report-citations-prose { line-height: 1.65; max-width: 100%; }
/* Make Gradio’s in-flight progress ring a bit more noticeable on dense layouts */
.gradio-container .pending { opacity: 0.92; }
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
    """After upload/change: show a loading line, then classified file summary (PDF / image / audio)."""
    yield "_⏳ **Loading files…** Resolving paths and detecting types (PDF, image, audio)…_"
    paths = collect_upload_paths(files)
    if not paths:
        yield "_No files attached. Upload PDFs, images, or audio when you are ready._"
        return
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
        lines.append(f"\n_Unclassified (could not sniff type): {len(skipped)} — check extensions or try another format._")
    yield "\n".join(lines)


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
    steps.append(f"Using {_llm_backend_label(settings)} for alignment check.")
    steps.append("Validating question and classifying uploads…")
    yield (
        gr.skip(),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(selected=TAB_TRACE),
        _preflight_trace_block(steps),
    )

    paths = collect_upload_paths(files)
    steps.append(f"Found {len(paths)} upload path(s); building digest (captions / PDF excerpts)…")
    yield (
        gr.skip(),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(selected=TAB_TRACE),
        _preflight_trace_block(steps),
    )

    try:
        steps.append("Calling the model for upload ↔ question alignment…")
        yield (
            gr.skip(),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(selected=TAB_TRACE),
            _preflight_trace_block(steps),
        )
        md = human_preflight_markdown(q, paths, settings)
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc
    except Exception as exc:
        raise gr.Error(f"Preflight failed: {exc!s}") from exc

    steps.append("Preflight complete — open **Human review** to read the summary.")
    yield (
        md,
        gr.update(visible=True),
        gr.update(visible=True),
        gr.update(selected=TAB_HUMAN),
        _preflight_trace_block(steps),
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
        f"- _Compiling graph and starting LangGraph stream…_\n"
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
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(selected=TAB_TRACE),
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
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(selected=TAB_TRACE),
                )
        if not saw_chunk:
            last_state = graph.invoke(initial_state)
    except Exception as exc:
        raise gr.Error(f"Research failed: {exc!s}") from exc

    fin = finalize_research_outputs(last_state)
    yield (
        *fin,
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(selected=TAB_REPORT),
    )


def _app_ready_message():
    return "_UI loaded. Pick an LLM backend, add files, then **Review** or run research — buttons show a spinner while work is in progress._"


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Local Multi-Agent Deep Researcher", css=REPORT_CITATION_CSS) as demo:
        gr.Markdown(
            """
# Local Multi-Agent Deep Researcher
A local-first, LangGraph-based research assistant derived from your original RAG notebook.

Reports lead with a **detailed narrative** with **inline, clickable citations** (styled as chips in the Report tab). Full references and per-channel notes follow below that.

**Human in the loop:** Click **Review uploads & question** first. The **Trace** tab opens immediately and logs each preflight step; your digest and alignment note appear under **Human review**. After **Yes — run full research**, the Trace tab streams **live pipeline progress** until the **Report** tab opens with results.

**LLM backend:** Choose **OpenRouter** or **Anthropic** below, paste the matching API key, then pick a model. OpenRouter exposes many providers; Anthropic lists **Haiku-only** (cheapest) Claude models. You can also set `LLM_PROVIDER` and keys in `.env`.

**Phase 2:** Up to **2 analyst passes** — pass 2 adds **gap planner**, **follow-up retrieval**, and a second critical analysis (higher latency/cost).
"""
        )

        with gr.Row():
            with gr.Column(scale=3):
                with gr.Accordion("LLM provider & API key", open=False):
                    llm_provider = gr.Radio(
                        label="1. Choose backend",
                        choices=[
                            ("OpenRouter — many models via one gateway", LLM_PROVIDER_OPENROUTER),
                            ("Anthropic — Claude Haiku only (cheapest tier)", LLM_PROVIDER_ANTHROPIC),
                        ],
                        value=LLM_PROVIDER_OPENROUTER,
                    )
                    gr.Markdown("_2. Paste the API key for the backend you selected (or rely on `.env`). 3. Pick a model._")
                    with gr.Column(visible=True) as openrouter_panel:
                        openrouter_key = gr.Textbox(
                            label="OpenRouter API key",
                            type="password",
                            placeholder="sk-or-… (empty → OPENROUTER_API_KEY from environment)",
                        )
                        openrouter_model = gr.Dropdown(
                            label="OpenRouter model",
                            choices=OPENROUTER_MODEL_PRESETS,
                            value="openai/gpt-4o-mini",
                            allow_custom_value=True,
                        )
                    with gr.Column(visible=False) as anthropic_panel:
                        anthropic_key = gr.Textbox(
                            label="Anthropic API key",
                            type="password",
                            placeholder="sk-ant-… (empty → ANTHROPIC_API_KEY from environment)",
                        )
                        anthropic_model = gr.Dropdown(
                            label="Claude model (budget / Haiku only)",
                            choices=list(ANTHROPIC_BUDGET_MODELS),
                            value=ANTHROPIC_BUDGET_MODELS[0],
                        )
                question = gr.Textbox(
                    label="Research question",
                    lines=5,
                    placeholder="Example: Compare how RAG and agentic retrieval differ in enterprise research workflows, using my uploaded PDFs plus current external evidence.",
                )
                files = gr.File(
                    label="Upload PDF, image, or audio files",
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
                    value="_No files yet. After you choose files, this row shows a **loading** state, then a short readiness summary._"
                )
                planner_objective = gr.Markdown(value="_Run a research job to show the planner objective._")

                enable_web_search = gr.Checkbox(
                    label="Enable web search via Tavily (recommended if key is configured)",
                    value=True,
                )

                with gr.Row():
                    top_k = gr.Slider(
                        label="Top-K local retrieval (FAISS)",
                        minimum=2,
                        maximum=8,
                        step=1,
                        value=4,
                    )
                    web_results_per_query = gr.Slider(
                        label="Web results per query",
                        minimum=1,
                        maximum=5,
                        step=1,
                        value=3,
                    )

                max_research_rounds = gr.Slider(
                    label="Max analyst passes (1 = single pass; 2 = gap planner + follow-up retrieval + 2nd analyst)",
                    minimum=1,
                    maximum=2,
                    step=1,
                    value=1,
                )

                review_button = gr.Button("1. Review uploads & question", variant="primary")
                with gr.Row():
                    confirm_yes = gr.Button(
                        "2. Yes — run full research", variant="primary", visible=False
                    )
                    confirm_no = gr.Button("No — cancel", variant="secondary", visible=False)

            with gr.Column(scale=4):
                ui_ready_md = gr.Markdown(value="_Loading interface…_")
                gr.Markdown(
                    "_Use the **Human review** tab for captions, PDF excerpts, and alignment after you click **Review**._"
                )
                with gr.Tabs(selected=TAB_HUMAN) as main_tabs:
                    with gr.Tab("Human review"):
                        human_review_md = gr.Markdown(
                            value=(
                                "_Click **1. Review uploads & question** to see image captions, PDF excerpts, "
                                "and an alignment check. Then confirm with **2. Yes — run full research**._"
                            )
                        )
                    with gr.Tab("Report"):
                        with gr.Column(elem_classes=["report-citations-prose"]):
                            gr.Markdown(
                                "_Inline source links use rounded chips (hover to read the domain). "
                                "Scroll past the narrative for the numbered **References** list and appendix._"
                            )
                            report = gr.Markdown()
                            gr.Markdown("**Contradictions**")
                            contradictions = gr.Markdown()
                            download_report = gr.File(label="Download markdown report")
                    with gr.Tab("Sources"):
                        gr.Markdown("Evidence catalog includes a truncated **excerpt** per row. Full snippets below.")
                        evidence_table = gr.Dataframe(label="Evidence catalog", interactive=False)
                        sources_detail_md = gr.Markdown(value="_Detailed extracts appear after a run._")
                    with gr.Tab("Trace & gaps"):
                        gaps_panel = gr.Markdown(value="_Gap planner output appears when using 2 analyst passes._")
                        trace_md = gr.Markdown()

        llm_inputs = [
            llm_provider,
            openrouter_key,
            openrouter_model,
            anthropic_key,
            anthropic_model,
        ]

        llm_provider.change(
            fn=_toggle_provider_panels,
            inputs=[llm_provider],
            outputs=[openrouter_panel, anthropic_panel],
            show_progress="minimal",
        )

        files.change(
            fn=on_files_updated,
            inputs=[files],
            outputs=[file_upload_status],
            show_progress="full",
        )

        review_button.click(
            fn=run_preflight_review,
            inputs=[question, files, *llm_inputs],
            outputs=[human_review_md, confirm_yes, confirm_no, main_tabs, trace_md],
            show_progress="full",
        )

        confirm_no.click(
            fn=cancel_preflight_review,
            inputs=[],
            outputs=[human_review_md, confirm_yes, confirm_no],
            show_progress="minimal",
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
            ],
            show_progress="full",
        )

        demo.load(
            fn=_app_ready_message,
            inputs=[],
            outputs=[ui_ready_md],
            show_progress="minimal",
        )

    return demo


if __name__ == "__main__":
    import os

    server_name = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")
    server_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))

    app = build_ui()
    app.launch(server_name=server_name, server_port=server_port, share=True)
