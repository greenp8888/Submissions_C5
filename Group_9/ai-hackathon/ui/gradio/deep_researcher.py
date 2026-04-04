from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import gradio as gr

from ai_app.domain.enums import DatePreset, RunMode, SourceChannel
from ui.components.agent_trace_view import render_trace
from ui.components.citation_panel import render_citations
from ui.components.confidence_badge import render_confidence_summary
from ui.components.evidence_table import render_claim_table
from ui.components.graph_panel import render_graph
from ui.components.query_input import DEPTH_CHOICES
from ui.components.report_viewer import render_report
from ui.components.run_timeline import render_events
from ui.components.source_list import render_sources


def build_app(coordinator):
    SOURCE_CHOICES = [
        ("Local RAG", SourceChannel.LOCAL_RAG.value),
        ("Web / Tavily", SourceChannel.WEB.value),
        ("arXiv", SourceChannel.ARXIV.value),
    ]

    def provider_status_markdown():
        payload = coordinator.provider_settings_payload(include_values=False)
        return (
            "### Provider Status\n"
            f"- OpenRouter: {payload['openrouter']['status']} | model={payload['openrouter']['model']}\n"
            f"- Tavily: {payload['tavily']['status']}\n"
            f"- arXiv: {payload['arxiv']['status']} ({payload['arxiv']['note']})"
        )

    def preset_dates(preset_value):
        today = date.today()
        preset = DatePreset(preset_value)
        if preset == DatePreset.ALL_TIME:
            return "", ""
        if preset == DatePreset.LAST_30_DAYS:
            start = today - timedelta(days=30)
        elif preset == DatePreset.LAST_90_DAYS:
            start = today - timedelta(days=90)
        elif preset == DatePreset.LAST_1_YEAR:
            start = today - timedelta(days=365)
        else:
            start = today - timedelta(days=365 * 5)
        return start.isoformat(), today.isoformat()

    def build_target_choices(session):
        choices = []
        for finding in session.findings[:15]:
            choices.append((f"Finding: {finding.id} :: {finding.content[:80]}", finding.id))
        for claim in session.claims[:15]:
            choices.append((f"Claim: {claim.id} :: {claim.statement[:80]}", claim.id))
        for insight in session.insights[:15]:
            choices.append((f"Insight: {insight.id} :: {insight.label}", insight.id))
        return choices

    def session_outputs(session):
        return (
            render_events([event.model_dump(mode="json") for event in session.events]),
            render_report([section.model_dump(mode="json") for section in session.report_sections]),
            render_confidence_summary([claim.model_dump(mode="json") for claim in session.claims]),
            render_sources([source.model_dump(mode="json") for source in session.sources]),
            render_citations([source.model_dump(mode="json") for source in session.sources]),
            render_graph([node.model_dump(mode="json") for node in session.entities], [edge.model_dump(mode="json") for edge in session.relationships]),
            render_trace([trace.model_dump(mode="json") for trace in session.agent_trace]),
            render_claim_table([claim.model_dump(mode="json") for claim in session.claims]),
            gr.update(choices=build_target_choices(session)),
        )

    async def refresh_collections():
        collections = coordinator.ingestion_service.list_collections()
        return gr.update(choices=[(collection.name, collection.id) for collection in collections])

    def current_provider_values():
        payload = coordinator.provider_settings_payload(include_values=True)
        return (
            payload["openrouter"].get("api_key", ""),
            payload["tavily"].get("api_key", ""),
            provider_status_markdown(),
        )

    def save_provider_settings(openrouter_key, tavily_key):
        coordinator.update_provider_keys(openrouter_key, tavily_key, persist=True)
        return provider_status_markdown()

    async def run_research(query, batch_topics_text, run_mode, enabled_sources, date_preset, start_date, end_date, depth, collection_ids, files):
        upload_payloads = []
        for file in files or []:
            with open(file.name, "rb") as handle:
                upload_payloads.append((Path(file.name).name, handle.read()))
        from ai_app.schemas.research import ResearchRequest

        batch_topics = [line.strip() for line in (batch_topics_text or "").splitlines() if line.strip()]
        request = ResearchRequest(
            query=query,
            depth=depth,
            collection_ids=collection_ids or [],
            use_local_corpus=SourceChannel.LOCAL_RAG.value in (enabled_sources or []),
            enabled_sources=enabled_sources or [],
            start_date=start_date or None,
            end_date=end_date or None,
            date_preset=date_preset,
            batch_topics=batch_topics,
            run_mode=run_mode,
        )
        session = await (coordinator.run_uploaded_research(request, upload_payloads) if upload_payloads else coordinator.start_background_research(request))
        queue = coordinator.session_store.queue(session.session_id)
        while True:
            event = await queue.get()
            current = coordinator.session_store.get(session.session_id)
            yield (
                session.session_id,
                *session_outputs(current),
            )
            if event.event_type in {"complete", "error"}:
                break

    async def dig_deeper(session_id_value, target_id):
        if not session_id_value or not target_id:
            return (
                "Provide a session ID and choose a finding/claim/insight target.",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                [],
                gr.update(),
            )
        session = await coordinator.dig_deeper(session_id_value, target_id)
        return (f"Dig deeper completed for {target_id}.", *session_outputs(session))

    def export_markdown(session_id_value):
        if not session_id_value:
            return None
        session = coordinator.session_store.get(session_id_value)
        export_dir = coordinator.settings.data_dir / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        path = export_dir / f"{session_id_value}.md"
        path.write_bytes(coordinator.export_service.markdown_bytes(coordinator.report_service.render_markdown(session)))
        return str(path)

    def export_pdf(session_id_value):
        if not session_id_value:
            return None
        session = coordinator.session_store.get(session_id_value)
        export_dir = coordinator.settings.data_dir / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        path = export_dir / f"{session_id_value}.pdf"
        path.write_bytes(coordinator.export_service.pdf_bytes(coordinator.report_service.render_markdown(session)))
        return str(path)

    with gr.Blocks(
        title="AI Hackathon Deep Researcher",
        css="""
        .app-shell {max-width: 1320px; margin: 0 auto;}
        .panel {border: 1px solid #d7d9e0; border-radius: 16px; padding: 14px; background: linear-gradient(180deg, #ffffff 0%, #f7f8fb 100%);}
        .hero h1 {margin-bottom: 0.2rem;}
        """,
    ) as demo:
        with gr.Column(elem_classes=["app-shell"]):
            gr.Markdown(
                """
                <div class="hero">
                <h1>Multi-Agent AI Deep Researcher</h1>
                <p>Run credible, source-selectable research with local RAG, web, and arXiv evidence. Every report preserves links, credibility rationale, and local page-level references where available.</p>
                </div>
                """
            )
            session_id = gr.Textbox(label="Session ID", interactive=False)
            with gr.Row():
                with gr.Column(scale=5, elem_classes=["panel"]):
                    gr.Markdown("## Research Setup")
                    query = gr.Textbox(label="Research Question", lines=4, placeholder="Ask a complex research question...")
                    run_mode = gr.Radio(
                        choices=[(mode.value.title(), mode.value) for mode in RunMode],
                        value=RunMode.SINGLE.value,
                        label="Run Mode",
                    )
                    batch_topics = gr.Textbox(
                        label="Batch Topics",
                        lines=5,
                        placeholder="One topic per line for batch mode.",
                    )
                    enabled_sources = gr.CheckboxGroup(
                        label="Sources",
                        choices=SOURCE_CHOICES,
                        value=[value for _, value in SOURCE_CHOICES],
                    )
                    with gr.Row():
                        date_preset = gr.Dropdown(
                            label="Quick Date Preset",
                            choices=[(preset.value.replace("_", " ").title(), preset.value) for preset in DatePreset],
                            value=DatePreset.ALL_TIME.value,
                        )
                        depth = gr.Radio(DEPTH_CHOICES, value="standard", label="Depth")
                    with gr.Row():
                        start_date = gr.Textbox(label="Start Date", placeholder="YYYY-MM-DD")
                        end_date = gr.Textbox(label="End Date", placeholder="YYYY-MM-DD")
                    with gr.Row():
                        collection_ids = gr.Dropdown(label="Collections", multiselect=True, choices=[])
                        refresh = gr.Button("Refresh Collections")
                    files = gr.File(label="Upload Local Research Files", file_count="multiple", file_types=[".pdf", ".txt", ".md"])
                    start = gr.Button("Start Research", variant="primary")
                with gr.Column(scale=3, elem_classes=["panel"]):
                    gr.Markdown("## Provider Configuration")
                    gr.Markdown("OpenRouter and Tavily are optional. arXiv is enabled by default and does not require an API key.")
                    openrouter_key = gr.Textbox(label="OpenRouter API Key", type="password")
                    tavily_key = gr.Textbox(label="Tavily API Key", type="password")
                    save_provider_button = gr.Button("Save Provider Settings")
                    provider_status = gr.Markdown()
                    gr.Markdown("## Follow-up Research")
                    dig_deeper_id = gr.Dropdown(label="Dig Deeper Target", choices=[], allow_custom_value=False)
                    dig_deeper_button = gr.Button("Dig Deeper")
                    dig_deeper_status = gr.Textbox(label="Dig Deeper Status", interactive=False)
                    gr.Markdown("## Export")
                    export_md = gr.Button("Export Markdown")
                    export_pdf_btn = gr.Button("Export PDF")
                    md_file = gr.File(label="Markdown Export")
                    pdf_file = gr.File(label="PDF Export")
            with gr.Row():
                with gr.Column(scale=4, elem_classes=["panel"]):
                    gr.Markdown("## Research Progress")
                    timeline = gr.Textbox(label="Planner / Retrieval / Analysis Timeline", lines=18)
                with gr.Column(scale=6, elem_classes=["panel"]):
                    gr.Markdown("## Report")
                    report = gr.Markdown()
            with gr.Tabs():
                with gr.Tab("References"):
                    with gr.Row():
                        with gr.Column():
                            source_list = gr.Markdown()
                        with gr.Column():
                            citations = gr.Markdown()
                with gr.Tab("Confidence"):
                    confidence = gr.Markdown()
                    claims_table = gr.Dataframe(
                        headers=["Claim", "Supporting Sources", "Contradicting Sources", "Confidence", "Trust", "Credibility Summary", "Evidence Summary"],
                        datatype=["str"] * 7,
                    )
                with gr.Tab("Graph"):
                    graph = gr.HTML()
                with gr.Tab("Trace"):
                    trace = gr.Markdown()

        refresh.click(fn=refresh_collections, outputs=collection_ids)
        date_preset.change(fn=preset_dates, inputs=date_preset, outputs=[start_date, end_date])
        start.click(
            fn=run_research,
            inputs=[query, batch_topics, run_mode, enabled_sources, date_preset, start_date, end_date, depth, collection_ids, files],
            outputs=[session_id, timeline, report, confidence, source_list, citations, graph, trace, claims_table, dig_deeper_id],
        )
        demo.load(fn=refresh_collections, outputs=collection_ids)
        demo.load(fn=current_provider_values, outputs=[openrouter_key, tavily_key, provider_status])
        save_provider_button.click(fn=save_provider_settings, inputs=[openrouter_key, tavily_key], outputs=provider_status)
        dig_deeper_button.click(
            fn=dig_deeper,
            inputs=[session_id, dig_deeper_id],
            outputs=[dig_deeper_status, timeline, report, confidence, source_list, citations, graph, trace, claims_table, dig_deeper_id],
        )
        export_md.click(fn=export_markdown, inputs=session_id, outputs=md_file)
        export_pdf_btn.click(fn=export_pdf, inputs=session_id, outputs=pdf_file)
    return demo
