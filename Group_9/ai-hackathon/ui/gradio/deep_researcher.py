from __future__ import annotations

from pathlib import Path

import gradio as gr

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
    async def refresh_collections():
        collections = coordinator.ingestion_service.list_collections()
        return gr.update(choices=[(collection.name, collection.id) for collection in collections])

    async def run_research(query, depth, collection_ids, files):
        upload_payloads = []
        for file in files or []:
            with open(file.name, "rb") as handle:
                upload_payloads.append((Path(file.name).name, handle.read()))
        from ai_app.schemas.research import ResearchRequest

        request = ResearchRequest(query=query, depth=depth, collection_ids=collection_ids or [], use_local_corpus=True)
        session = await (coordinator.run_uploaded_research(request, upload_payloads) if upload_payloads else coordinator.start_background_research(request))
        queue = coordinator.session_store.queue(session.session_id)
        events = []
        while True:
            event = await queue.get()
            events.append(event.model_dump(mode="json"))
            current = coordinator.session_store.get(session.session_id)
            yield (
                session.session_id,
                render_events(events),
                render_report([section.model_dump(mode="json") for section in current.report_sections]),
                render_confidence_summary([claim.model_dump(mode="json") for claim in current.claims]),
                render_sources([source.model_dump(mode="json") for source in current.sources]),
                render_citations([source.model_dump(mode="json") for source in current.sources]),
                render_graph([node.model_dump(mode="json") for node in current.entities], [edge.model_dump(mode="json") for edge in current.relationships]),
                render_trace([trace.model_dump(mode="json") for trace in current.agent_trace]),
                render_claim_table([claim.model_dump(mode="json") for claim in current.claims]),
            )
            if event.event_type in {"complete", "error"}:
                break

    async def dig_deeper(session_id_value, target_id):
        if not session_id_value or not target_id:
            return "Provide a session ID and a finding/claim/insight ID."
        await coordinator.dig_deeper(session_id_value, target_id)
        return f"Dig deeper triggered for {target_id} in {session_id_value}."

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

    with gr.Blocks(title="AI Hackathon Deep Researcher") as demo:
        gr.Markdown("# Multi-Agent AI Deep Researcher")
        session_id = gr.Textbox(label="Session ID", interactive=False)
        with gr.Row():
            query = gr.Textbox(label="Research Question", lines=3, placeholder="Ask a complex research question...")
            with gr.Column():
                depth = gr.Radio(DEPTH_CHOICES, value="standard", label="Depth")
                collection_ids = gr.Dropdown(label="Collections", multiselect=True, choices=[])
                refresh = gr.Button("Refresh Collections")
        files = gr.File(label="Upload Research Files", file_count="multiple", file_types=[".pdf", ".txt", ".md"])
        start = gr.Button("Start Research", variant="primary")
        with gr.Row():
            dig_deeper_id = gr.Textbox(label="Dig Deeper Target ID", placeholder="finding_id / claim_id / insight_id")
            dig_deeper_button = gr.Button("Dig Deeper")
            dig_deeper_status = gr.Textbox(label="Dig Deeper Status", interactive=False)
        with gr.Row():
            export_md = gr.Button("Export Markdown")
            export_pdf_btn = gr.Button("Export PDF")
            md_file = gr.File(label="Markdown Export")
            pdf_file = gr.File(label="PDF Export")
        with gr.Tabs():
            with gr.Tab("Timeline"):
                timeline = gr.Textbox(label="Progress", lines=16)
            with gr.Tab("Report"):
                report = gr.Markdown()
            with gr.Tab("Confidence"):
                confidence = gr.Markdown()
                claims_table = gr.Dataframe(headers=["Claim", "Supporting Sources", "Contradicting Sources", "Confidence", "Trust"], datatype=["str"] * 5)
            with gr.Tab("Sources"):
                source_list = gr.Markdown()
                citations = gr.Markdown()
            with gr.Tab("Graph"):
                graph = gr.HTML()
            with gr.Tab("Trace"):
                trace = gr.Markdown()

        refresh.click(fn=refresh_collections, outputs=collection_ids)
        start.click(
            fn=run_research,
            inputs=[query, depth, collection_ids, files],
            outputs=[session_id, timeline, report, confidence, source_list, citations, graph, trace, claims_table],
        )
        demo.load(fn=refresh_collections, outputs=collection_ids)
        dig_deeper_button.click(fn=dig_deeper, inputs=[session_id, dig_deeper_id], outputs=dig_deeper_status)
        export_md.click(fn=export_markdown, inputs=session_id, outputs=md_file)
        export_pdf_btn.click(fn=export_pdf, inputs=session_id, outputs=pdf_file)
    return demo
