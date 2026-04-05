
from __future__ import annotations

import tempfile
from pathlib import Path

import gradio as gr
import pandas as pd

from deep_researcher.config import Settings
from deep_researcher.graph import build_graph


def create_downloadable_report(markdown_text: str) -> str:
    output_dir = Path(tempfile.mkdtemp(prefix="deep_research_report_"))
    output_path = output_dir / "research_report.md"
    output_path.write_text(markdown_text, encoding="utf-8")
    return str(output_path)


def evidence_to_dataframe(evidence: list[dict]) -> pd.DataFrame:
    if not evidence:
        return pd.DataFrame(
            columns=[
                "source_type",
                "source_label",
                "title",
                "url",
                "query_used",
                "relevance_hint",
            ]
        )

    rows = []
    for item in evidence:
        rows.append(
            {
                "source_type": item.get("source_type", ""),
                "source_label": item.get("source_label", ""),
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "query_used": item.get("query_used", ""),
                "relevance_hint": item.get("relevance_hint", ""),
            }
        )
    return pd.DataFrame(rows)


DETAILED_ANALYSIS_PLACEHOLDER = (
    "_Click **Detailed Analysis** after a run to show **Detailed extracts (all retrieved snippets)** below._"
)

DETAILED_EXTRACTS_COLLAPSED = (
    "_Detailed extracts are **hidden**. Click **Detailed Analysis** again to show them._"
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


def run_research(
    question: str,
    files,
    enable_web_search: bool,
    top_k: int,
    web_results_per_query: int,
):
    question = (question or "").strip()
    if not question:
        raise gr.Error("Please enter a research question.")

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
        "trace": ["Research request accepted by the orchestrator."],
        "retrieval_log": [],
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
    download_markdown = (
        f"{report}\n\n---\n\n{detailed_md}" if detailed_md else report
    )
    download_path = create_downloadable_report(download_markdown)

    return (
        report,
        evidence_df,
        trace_md,
        contradictions_md,
        download_path,
        detailed_md,
        DETAILED_ANALYSIS_PLACEHOLDER,
        False,
    )


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Local Multi-Agent Deep Researcher") as demo:
        gr.Markdown(
            """
# Local Multi-Agent Deep Researcher
A local-first, LangGraph-based research assistant derived from your original RAG notebook.

Use it for:
- uploaded PDFs, images (e.g. PNG/JPG), and audio (transcribed with Whisper)
- web-assisted research
- paper/background synthesis
- contradiction spotting
- report generation
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

                run_button = gr.Button("Run deep research", variant="primary")

            with gr.Column(scale=4):
                report = gr.Markdown()
                contradictions = gr.Markdown()
                download_report = gr.File(label="Download markdown report")
                detailed_extracts_md = gr.Markdown(value=DETAILED_ANALYSIS_PLACEHOLDER)
                detailed_analysis_btn = gr.Button("Detailed Analysis")

        with gr.Accordion("Evidence and execution trace", open=False):
            evidence_table = gr.Dataframe(label="Evidence catalog", interactive=False)
            trace_md = gr.Markdown()

        detailed_extracts_store = gr.State("")
        detailed_extracts_visible = gr.State(False)

        def toggle_detailed_extracts(is_visible: bool, stored: str) -> tuple[str, bool]:
            text = (stored or "").strip()
            if not text:
                return (
                    "_Run **Run deep research** first, then click **Detailed Analysis**._",
                    False,
                )
            if is_visible:
                return DETAILED_EXTRACTS_COLLAPSED, False
            return stored, True

        run_button.click(
            fn=run_research,
            inputs=[question, files, enable_web_search, top_k, web_results_per_query],
            outputs=[
                report,
                evidence_table,
                trace_md,
                contradictions,
                download_report,
                detailed_extracts_store,
                detailed_extracts_md,
                detailed_extracts_visible,
            ],
        )

        detailed_analysis_btn.click(
            fn=toggle_detailed_extracts,
            inputs=[detailed_extracts_visible, detailed_extracts_store],
            outputs=[detailed_extracts_md, detailed_extracts_visible],
        )

    return demo


if __name__ == "__main__":
    import os

    server_name = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")
    server_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))

    app = build_ui()
    app.launch(server_name=server_name, server_port=server_port, share=True)
