from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

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
from ai_app.domain.enums import ResearchStatus
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
        analysis = CriticalAnalysisAgent(SourceVerifierAgent(), ContradictionCheckerAgent())
        insights = InsightGenerationAgent(HypothesisAgent())
        reporter = ReportBuilderAgent()
        self.qa_review = QAReviewAgent()

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

    def _wrap_node(self, label: str, node_fn: Callable[[ResearchSession], Awaitable[ResearchSession]]):
        async def wrapped(state):
            session = state["session"]
            await self.emit(session.session_id, ResearchEvent(event_type="status", agent=label, message=f"Running {label}"))
            self.trace(session.session_id, AgentTraceEntry(agent=label, step=f"{label}_start", input_summary=session.query, token_estimate=50))
            updated = await node_fn(session)
            self.trace(
                updated.session_id,
                AgentTraceEntry(agent=label, step=f"{label}_complete", output_summary=f"sources={len(updated.sources)} claims={len(updated.claims)}", token_estimate=80),
            )
            return {"session": updated}

        return wrapped

    def create_session(self, request: ResearchRequest) -> ResearchSession:
        session = ResearchSession(query=request.query, depth=request.depth, selected_collection_ids=request.collection_ids)
        return self.session_store.create(session)

    async def emit(self, session_id: str, event: ResearchEvent) -> None:
        await self.session_store.emit(session_id, event)

    def trace(self, session_id: str, trace: AgentTraceEntry) -> None:
        self.session_store.trace(session_id, trace)

    async def run_research(self, session: ResearchSession) -> ResearchSession:
        session.status = ResearchStatus.RUNNING
        self.session_store.save(session)
        try:
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
        follow_up = ResearchSession(
            query=focus_query,
            depth=session.depth,
            selected_collection_ids=session.selected_collection_ids,
            uploaded_documents=session.uploaded_documents,
            pdf_texts=session.pdf_texts,
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
        session.report_sections = result.report_sections
        self.session_store.save(session)
        return session

