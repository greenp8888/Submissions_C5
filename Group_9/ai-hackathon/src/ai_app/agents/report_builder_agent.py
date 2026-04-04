from __future__ import annotations

from ai_app.agents.base import AgentBase
from ai_app.retrieval.citation_builder import format_inline_citations, order_sources_for_citation
from ai_app.schemas.research import ReportSection, ResearchSession


class ReportBuilderAgent(AgentBase):
    name = "report_builder_agent"

    async def run(self, session: ResearchSession) -> ResearchSession:
        ordered_sources = order_sources_for_citation(session.sources)
        summary = session.claims[0].statement if session.claims else "Research session completed with limited evidence."
        key_findings = "\n".join(
            f"- {claim.statement} (confidence: {claim.confidence.value}, trust: {claim.trust_score}%)"
            for claim in session.claims[:6]
        ) or "- No claims generated."
        contested = "\n".join(f"- {item.analysis}" for item in session.contradictions[:5]) or "- No major contradictions detected."
        insights = "\n".join(f"- {insight.label}: {insight.content}" for insight in session.insights[:5]) or "- No insights generated."
        follow_ups = "\n".join(f"- {question.question}" for question in session.follow_up_questions[:5])
        appendix = "\n".join(
            f"- {source.title} [{source.provider}] ({source.source_type.value})"
            for source in ordered_sources[:15]
        ) or "- No sources collected."
        session.report_sections = [
            ReportSection(section_type="summary", title="Executive Summary", content=f"{summary}\n\nCitations: {format_inline_citations(ordered_sources[:4])}", order=1),
            ReportSection(section_type="findings", title="Key Findings", content=key_findings, order=2),
            ReportSection(section_type="contested", title="Contested Claims", content=contested, order=3),
            ReportSection(section_type="insights", title="Insights", content=insights, order=4),
            ReportSection(section_type="follow_up", title="Follow-Up Questions", content=follow_ups or "- No follow-up questions.", order=5),
            ReportSection(section_type="appendix", title="Source Appendix", content=appendix, order=6),
        ]
        return session
