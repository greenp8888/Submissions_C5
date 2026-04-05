from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import date, timedelta
from pathlib import Path

from ai_app.agents.academic_expansion_retriever import AcademicExpansionRetriever
from ai_app.agents.academic_retriever import AcademicRetriever
from ai_app.agents.contextual_retriever_agent import ContextualRetrieverAgent
from ai_app.agents.contradiction_checker_agent import ContradictionCheckerAgent
from ai_app.agents.critical_analysis_agent import CriticalAnalysisAgent
from ai_app.agents.hypothesis_agent import HypothesisAgent
from ai_app.agents.insight_generation_agent import InsightGenerationAgent
from ai_app.agents.local_retriever import LocalRetriever
from ai_app.agents.news_expansion_retriever import NewsExpansionRetriever
from ai_app.agents.news_retriever import NewsRetriever
from ai_app.agents.pdf_retriever import PDFFallbackRetriever
from ai_app.agents.planner_agent import PlannerAgent
from ai_app.agents.qa_review_agent import QAReviewAgent
from ai_app.agents.report_api_retriever import ReportAPIRetriever
from ai_app.agents.report_builder_agent import ReportBuilderAgent
from ai_app.agents.source_verifier_agent import SourceVerifierAgent
from ai_app.agents.web_retriever import WebRetriever
from ai_app.config import Settings
from ai_app.domain.enums import DatePreset, ResearchStatus, RunMode, SourceChannel
from ai_app.llms.client import OpenRouterClient
from ai_app.memory.session_store import SessionStore
from ai_app.orchestration.graph import build_graph
from ai_app.schemas.research import (
    AgentTraceEntry,
    LocalCollection,
    ResearchEvent,
    ResearchRequest,
    ResearchSession,
)
from ai_app.retrieval.local_index import LocalIndex
from ai_app.services.document_ingestion_service import DocumentIngestionService
from ai_app.services.export_service import ExportService
from ai_app.services.report_service import ReportService


class ResearchCoordinator:
    def __init__(self, settings: Settings, session_store: SessionStore) -> None:
        self.settings = settings
        self.session_store = session_store
        self.local_index = LocalIndex(settings)
        self.ingestion_service = DocumentIngestionService(settings, self.local_index)
        self.report_service = ReportService()
        self.export_service = ExportService()
        self.llm_client = OpenRouterClient(settings)

        local_retriever = LocalRetriever(self.local_index, self.ingestion_service, settings.top_k)
        planner = PlannerAgent(self.llm_client)
        retriever = ContextualRetrieverAgent(
            local_retriever=local_retriever,
            pdf_retriever=PDFFallbackRetriever(),
            web_retriever=WebRetriever(settings),
            news_retriever=NewsRetriever(settings),
            academic_retriever=AcademicRetriever(),
            academic_expansion_retriever=AcademicExpansionRetriever(),
            news_expansion_retriever=NewsExpansionRetriever(),
            report_api_retriever=ReportAPIRetriever(),
            top_k=settings.top_k,
        )
        contradiction_checker = ContradictionCheckerAgent(self.llm_client)
        analysis = CriticalAnalysisAgent(self.llm_client, SourceVerifierAgent(), contradiction_checker)
        insights = InsightGenerationAgent(self.llm_client, HypothesisAgent())
        reporter = ReportBuilderAgent()
        self.qa_review = QAReviewAgent(self.llm_client)

        self._planner = planner
        self._retriever = retriever
        self._analysis = analysis
        self._insights = insights
        self._reporter = reporter
        self.graph = build_graph(
            self._wrap_node("planner", planner.run),
            self._wrap_node("retriever", retriever.run),
            self._wrap_node("analysis", analysis.run),
            self._wrap_node("insight", insights.run),
            self._wrap_node("reporter", reporter.run),
        )

    @property
    def env_file_path(self) -> Path:
        return Path(__file__).resolve().parents[3] / ".env"

    def _wrap_node(self, label: str, node_fn: Callable[[ResearchSession], Awaitable[ResearchSession]]):
        async def wrapped(state):
            session = state["session"]
            previous_sources = len(session.sources)
            previous_claims = len(session.claims)
            previous_sections = len(session.report_sections)
            await self.emit(session.session_id, ResearchEvent(event_type="status", agent=label, message=f"Running {label}"))
            self.trace(session.session_id, AgentTraceEntry(agent=label, step=f"{label}_start", input_summary=session.query, token_estimate=50))
            updated = await node_fn(session)
            self.trace(
                updated.session_id,
                AgentTraceEntry(agent=label, step=f"{label}_complete", output_summary=f"sources={len(updated.sources)} claims={len(updated.claims)}", token_estimate=80),
            )
            if label == "retriever":
                new_sources = updated.sources[previous_sources:]
                for source in new_sources[:20]:
                    await self.emit(
                        updated.session_id,
                        ResearchEvent(
                            event_type="finding",
                            agent=label,
                            message=f"Retrieved source: {source.title}",
                            data={
                                "provider": source.provider,
                                "title": source.title,
                                "url": source.url,
                                "filename": source.filename,
                                "credibility_score": source.credibility_score,
                                "credibility_explanation": source.credibility_explanation,
                            },
                        ),
                    )
            if label == "analysis":
                for claim in updated.claims[previous_claims:previous_claims + 10]:
                    await self.emit(
                        updated.session_id,
                        ResearchEvent(
                            event_type="claim",
                            agent=label,
                            message=f"Generated claim: {claim.statement}",
                            data={
                                "confidence": claim.confidence.value,
                                "trust_score": claim.trust_score,
                                "consensus_pct": claim.consensus_pct,
                                "debate_position": claim.debate_position or "neutral",
                            },
                        ),
                    )
            if label == "reporter":
                for section in updated.report_sections[previous_sections:]:
                    await self.emit(
                        updated.session_id,
                        ResearchEvent(
                            event_type="report_section",
                            agent=label,
                            message=f"Built report section: {section.title}",
                            data={"section_type": section.section_type},
                        ),
                    )
            return {"session": updated}

        return wrapped

    def _resolve_date_range(self, request: ResearchRequest) -> tuple[date | None, date | None]:
        if request.date_preset == DatePreset.ALL_TIME:
            return request.start_date, request.end_date
        end_date = request.end_date or date.today()
        if request.date_preset == DatePreset.LAST_30_DAYS:
            return end_date - timedelta(days=30), end_date
        if request.date_preset == DatePreset.LAST_90_DAYS:
            return end_date - timedelta(days=90), end_date
        if request.date_preset == DatePreset.LAST_1_YEAR:
            return end_date - timedelta(days=365), end_date
        if request.date_preset == DatePreset.LAST_5_YEARS:
            return end_date - timedelta(days=365 * 5), end_date
        return request.start_date, request.end_date

    def create_session(self, request: ResearchRequest) -> ResearchSession:
        start_date, end_date = self._resolve_date_range(request)
        batch_topics = [topic.strip() for topic in request.batch_topics if topic.strip()]
        query = request.query.strip()
        if request.run_mode == RunMode.BATCH and batch_topics:
            query = f"Batch research covering: {', '.join(batch_topics)}"
        enabled_sources = list(request.enabled_sources)
        if not request.use_local_corpus:
            enabled_sources = [source for source in enabled_sources if source != SourceChannel.LOCAL_RAG]
        session = ResearchSession(
            query=query,
            run_mode=request.run_mode,
            batch_topics=batch_topics,
            enabled_sources=enabled_sources,
            start_date=start_date,
            end_date=end_date,
            date_preset=request.date_preset,
            depth=request.depth,
            selected_collection_ids=request.collection_ids,
            debate_mode=request.debate_enabled,
            position_a=request.position_a,
            position_b=request.position_b,
        )
        session.metadata["source_labels"] = [source.value for source in enabled_sources]
        session.metadata["date_range_label"] = (
            f"{start_date.isoformat()} to {end_date.isoformat()}" if start_date and end_date else request.date_preset.value
        )
        session.metadata["llm_model"] = self.settings.openrouter_model
        session.metadata["session_store"] = "sqlite"
        if request.debate_enabled:
            session.metadata["debate_enabled"] = True
        provider_warnings: list[str] = []
        if SourceChannel.WEB in enabled_sources and not self.settings.tavily_api_key:
            provider_warnings.append("Web and news search were enabled in the request, but Tavily is not configured because no TAVILY_API_KEY was loaded from .env or environment variables.")
        if not self.settings.openrouter_api_key:
            provider_warnings.append("OpenRouter is not configured, so the reasoning agents will use heuristic fallback behavior.")
        if provider_warnings:
            session.metadata["provider_warnings"] = provider_warnings
        return self.session_store.create(session)

    async def emit(self, session_id: str, event: ResearchEvent) -> None:
        await self.session_store.emit(session_id, event)

    def trace(self, session_id: str, trace: AgentTraceEntry) -> None:
        self.session_store.trace(session_id, trace)

    def provider_status(self) -> str:
        payload = self.provider_settings_payload(include_values=False)
        return (
            f"OpenRouter: {payload['openrouter']['status']}\n"
            f"Tavily: {payload['tavily']['status']}\n"
            "arXiv: enabled (no API key required)"
        )

    def provider_settings_payload(self, include_values: bool = False) -> dict[str, object]:
        payload = {
            "openrouter": {
                "status": "configured" if self.settings.openrouter_api_key else "not configured",
                "configured": bool(self.settings.openrouter_api_key),
                "model": self.settings.openrouter_model,
            },
            "tavily": {
                "status": "configured" if self.settings.tavily_api_key else "not configured",
                "configured": bool(self.settings.tavily_api_key),
            },
            "arxiv": {
                "status": "enabled",
                "configured": True,
                "note": "No API key required.",
            },
        }
        if include_values:
            payload["openrouter"]["api_key"] = self.settings.openrouter_api_key or ""
            payload["tavily"]["api_key"] = self.settings.tavily_api_key or ""
        return payload

    def update_provider_keys(self, openrouter_api_key: str | None, tavily_api_key: str | None, persist: bool = True) -> str:
        self.settings.openrouter_api_key = openrouter_api_key.strip() if openrouter_api_key else None
        self.settings.tavily_api_key = tavily_api_key.strip() if tavily_api_key else None
        if persist:
            self._persist_provider_keys()
        return self.provider_status()

    def _persist_provider_keys(self) -> None:
        lines: dict[str, str] = {}
        if self.env_file_path.exists():
            for raw_line in self.env_file_path.read_text(encoding="utf-8").splitlines():
                if "=" in raw_line and not raw_line.strip().startswith("#"):
                    key, value = raw_line.split("=", 1)
                    lines[key] = value
        lines["OPENROUTER_API_KEY"] = self.settings.openrouter_api_key or ""
        lines["TAVILY_API_KEY"] = self.settings.tavily_api_key or ""
        if "OPENROUTER_MODEL" not in lines:
            lines["OPENROUTER_MODEL"] = self.settings.openrouter_model
        if "AI_HACKATHON_DATA_DIR" not in lines:
            lines["AI_HACKATHON_DATA_DIR"] = str(self.settings.data_dir)
        if "AI_HACKATHON_TOP_K" not in lines:
            lines["AI_HACKATHON_TOP_K"] = str(self.settings.top_k)
        if "AI_HACKATHON_EMBED_DIM" not in lines:
            lines["AI_HACKATHON_EMBED_DIM"] = str(self.settings.embed_dim)
        payload = "\n".join(f"{key}={value}" for key, value in lines.items()) + "\n"
        self.env_file_path.write_text(payload, encoding="utf-8")

    async def run_research(self, session: ResearchSession) -> ResearchSession:
        session.status = ResearchStatus.RUNNING
        self.session_store.save(session)
        try:
            for warning in session.metadata.get("provider_warnings", []):
                await self.emit(session.session_id, ResearchEvent(event_type="status", agent="coordinator", message=warning))
            result = await self.graph.ainvoke({"session": session})
            session = result["session"]
            session = await self.qa_review.run(session)
            session.status = ResearchStatus.COMPLETE
            self.session_store.save(session)
            await self.emit(session.session_id, ResearchEvent(event_type="complete", message="Research complete"))
            return session
        except Exception as exc:
            session.status = ResearchStatus.ERROR
            session.metadata["error"] = str(exc)
            self.session_store.save(session)
            await self.emit(session.session_id, ResearchEvent(event_type="error", message=str(exc)))
            raise

    async def start_background_research(self, request: ResearchRequest) -> ResearchSession:
        session = self.create_session(request)
        asyncio.create_task(self.run_research(session))
        return session

    async def run_uploaded_research(self, request: ResearchRequest, files: list[tuple[str, bytes]]) -> ResearchSession:
        session = self.create_session(request)
        if files:
            collection = LocalCollection(name=f"Session {session.session_id}", description="Session upload")
            documents, _ = self.ingestion_service.ingest_files(collection, files)
            session.selected_collection_ids = [collection.id]
            session.uploaded_documents.extend(documents)
            session.pdf_texts.extend(document.summary for document in documents if document.document_type == "pdf")
        asyncio.create_task(self.run_research(session))
        return session

    async def dig_deeper(self, session_id: str, target_id: str) -> ResearchSession:
        session = self.session_store.get(session_id)
        focus_query = None
        for finding in session.findings:
            if finding.id == target_id:
                focus_query = finding.content
        for claim in session.claims:
            if claim.id == target_id:
                focus_query = claim.statement
        for insight in session.insights:
            if insight.id == target_id:
                focus_query = insight.content
        if not focus_query:
            raise KeyError(f"Unknown target: {target_id}")
        await self.emit(session.session_id, ResearchEvent(event_type="status", message=f"Dig deeper started for {target_id}", agent="dig_deeper"))
        follow_up = ResearchSession(
            query=focus_query,
            run_mode=RunMode.SINGLE,
            batch_topics=[],
            enabled_sources=session.enabled_sources,
            start_date=session.start_date,
            end_date=session.end_date,
            date_preset=session.date_preset,
            depth=session.depth,
            selected_collection_ids=session.selected_collection_ids,
            uploaded_documents=session.uploaded_documents,
            pdf_texts=session.pdf_texts,
            debate_mode=session.debate_mode,
            position_a=session.position_a,
            position_b=session.position_b,
        )
        result = await self.run_research(self.session_store.create(follow_up))
        session.sources.extend(result.sources)
        session.findings.extend(result.findings)
        session.claims.extend(result.claims)
        session.contradictions.extend(result.contradictions)
        session.insights.extend(result.insights)
        session.entities.extend(result.entities)
        session.relationships.extend(result.relationships)
        session.follow_up_questions.extend(result.follow_up_questions)
        session.events.extend(result.events)
        session.agent_trace.extend(result.agent_trace)
        session.report_sections = result.report_sections
        self.session_store.save(session)
        await self.emit(session.session_id, ResearchEvent(event_type="complete", message=f"Dig deeper completed for {target_id}", agent="dig_deeper"))
        return session
