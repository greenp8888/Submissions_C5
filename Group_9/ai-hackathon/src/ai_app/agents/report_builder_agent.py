from __future__ import annotations

from collections import defaultdict

from ai_app.agents.base import AgentBase
from ai_app.retrieval.citation_builder import format_inline_citations, format_reference_entry, order_sources_for_citation
from ai_app.schemas.research import ReportSection, ResearchSession


class ReportBuilderAgent(AgentBase):
    name = "report_builder_agent"

    async def run(self, session: ResearchSession) -> ResearchSession:
        ordered_sources = order_sources_for_citation(session.sources)
        source_map = {source.id: source for source in ordered_sources}

        summary = (
            session.claims[0].statement if session.claims else "Research session completed with limited evidence."
        )
        methodology = "\n".join(
            [
                f"- Query: {session.query}",
                f"- Depth: {session.depth.value}",
                f"- Sub-questions investigated: {len(session.sub_questions)}",
                f"- Sources collected: {len(ordered_sources)}",
                f"- Findings collected: {len(session.findings)}",
                f"- Claims generated: {len(session.claims)}",
                "- Retrieval policy: local corpus first, then public enrichment when local evidence is incomplete.",
            ]
        )

        findings_by_question: dict[str, list[str]] = defaultdict(list)
        for finding in session.findings:
            linked_sources = [source_map[source_id] for source_id in finding.source_ids if source_id in source_map]
            citation = format_inline_citations(linked_sources[:4]) if linked_sources else "No citation available"
            findings_by_question[finding.sub_question].append(f"- {finding.content}\n  Citations: {citation}")
        evidence_synthesis = "\n\n".join(
            f"### {question}\n" + "\n".join(entries[:5])
            for question, entries in findings_by_question.items()
        ) or "No evidence synthesis available."

        key_findings = "\n".join(
            f"- {claim.statement}\n  Confidence: {claim.confidence.value} ({claim.confidence_pct}%), Trust: {claim.trust_score}%\n  Citations: {format_inline_citations([source_map[source_id] for source_id in claim.supporting_source_ids if source_id in source_map][:4]) or 'No citation available'}"
            for claim in session.claims[:12]
        ) or "- No claims generated."

        contested = "\n".join(
            f"- {item.analysis}\n  Claim A: {item.claim_a}\n  Claim B: {item.claim_b}"
            for item in session.contradictions[:10]
        ) or "- No major contradictions detected."

        insights = "\n".join(
            f"- {insight.label}: {insight.content}\n  Evidence: {format_inline_citations([source_map[source_id] for source_id in insight.evidence_chain if source_id in source_map][:5]) or 'No citation available'}"
            for insight in session.insights[:10]
        ) or "- No insights generated."

        follow_ups = "\n".join(
            f"- {question.question}\n  Why it matters: {question.rationale}"
            for question in session.follow_up_questions[:8]
        ) or "- No follow-up questions."

        reference_list = "\n".join(
            f"- {format_reference_entry(source)}"
            for source in ordered_sources[:50]
        ) or "- No sources collected."

        web_and_papers = "\n".join(
            f"- [{source.title}]({source.url}) | provider={source.provider} | type={source.source_type.value}"
            for source in ordered_sources
            if source.url
        ) or "- No external links collected."

        session.report_sections = [
            ReportSection(section_type="summary", title="Executive Summary", content=f"{summary}\n\nPrimary citations: {format_inline_citations(ordered_sources[:8])}", order=1),
            ReportSection(section_type="methodology", title="Research Methodology", content=methodology, order=2),
            ReportSection(section_type="evidence_synthesis", title="Evidence Synthesis By Sub-Question", content=evidence_synthesis, order=3),
            ReportSection(section_type="findings", title="Detailed Findings And Claims", content=key_findings, order=4),
            ReportSection(section_type="contested", title="Contested Claims And Weak Evidence", content=contested, order=5),
            ReportSection(section_type="insights", title="Insights And Research Interpretation", content=insights, order=6),
            ReportSection(section_type="follow_up", title="Follow-Up Questions", content=follow_ups, order=7),
            ReportSection(section_type="links", title="Web And arXiv Links", content=web_and_papers, order=8),
            ReportSection(section_type="appendix", title="Comprehensive References", content=reference_list, order=9),
        ]
        return session
