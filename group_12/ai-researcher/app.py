
from __future__ import annotations

import tempfile
from pathlib import Path

import gradio as gr
import pandas as pd

from deep_researcher.config import Settings
from deep_researcher.graph import build_graph, normalize_excerpt_whitespace

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


def run_research(
    question: str,
    files,
    enable_web_search: bool,
    top_k: int,
    web_results_per_query: int,
    max_research_rounds: float,
):
    question = (question or "").strip()
    if not question:
        raise gr.Error("Please enter a research question.")

    rounds = int(min(2, max(1, int(max_research_rounds))))

    settings = Settings.load()
    graph = build_graph(settings)

    def _normalize_upload_path(f) -> str | None:
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

    local_paths: list[str] = []
    if files:
        iterable = files if isinstance(files, list) else [files]
        for f in iterable:
            p = _normalize_upload_path(f)
            if p:
                local_paths.append(p)

    initial_state = {
        "question": question,
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

    result = graph.invoke(initial_state)
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

    return (
        report,
        gaps_md,
        objective_md,
        evidence_df,
        trace_md,
        contradictions_md,
        download_path,
        detailed_md or "_No detailed extracts (nothing retrieved)._",
    )


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Local Multi-Agent Deep Researcher", css=REPORT_CITATION_CSS) as demo:
        gr.Markdown(
            """
# Local Multi-Agent Deep Researcher
A local-first, LangGraph-based research assistant derived from your original RAG notebook.

Reports lead with a **detailed narrative** with **inline, clickable citations** (styled as chips in the Report tab). Full references and per-channel notes follow below that.

**Phase 2:** Up to **2 analyst passes** — pass 2 adds **gap planner**, **follow-up retrieval**, and a second critical analysis (higher latency/cost).
"""
        )

        with gr.Row():
            with gr.Column(scale=3):
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

                run_button = gr.Button("Run deep research", variant="primary")

            with gr.Column(scale=4):
                with gr.Tabs():
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

        run_button.click(
            fn=run_research,
            inputs=[
                question,
                files,
                enable_web_search,
                top_k,
                web_results_per_query,
                max_research_rounds,
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
            ],
        )

    return demo


if __name__ == "__main__":
    import os

    server_name = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")
    server_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))

    app = build_ui()
    app.launch(server_name=server_name, server_port=server_port, share=True)
