from __future__ import annotations

from collections import defaultdict

from ai_app.agents.base import AgentBase
from ai_app.retrieval.citation_builder import format_inline_citations, format_reference_entry, order_sources_for_citation
from ai_app.retrieval.time_filters import describe_date_window
from ai_app.domain.enums import SourceChannel
from ai_app.schemas.research import ReportSection, ResearchSession


class ReportBuilderAgent(AgentBase):
    name = "report_builder_agent"

    async def run(self, session: ResearchSession) -> ResearchSession:
        ordered_sources = order_sources_for_citation(session.sources)
        source_map = {source.id: source for source in ordered_sources}
        rag_sources = [source for source in ordered_sources if source.provider == "local_rag"]
        web_sources = [source for source in ordered_sources if source.provider == "tavily" and source.source_type.value == "web"]
        news_sources = [source for source in ordered_sources if source.provider == "tavily" and source.source_type.value == "news"]
        arxiv_sources = [source for source in ordered_sources if source.provider == "arxiv"]
        enabled_sources = ", ".join(source.value for source in session.enabled_sources)
        date_window = describe_date_window(session.start_date, session.end_date)

        summary = (
            session.claims[0].statement if session.claims else "Research session completed with limited evidence."
        )
        methodology = "\n".join(
            [
                f"- Query: {session.query}",
                f"- Run mode: {session.run_mode.value}",
                f"- Depth: {session.depth.value}",
                f"- Enabled sources: {enabled_sources}",
                f"- Date window applied to external sources: {date_window}",
                f"- Sub-questions investigated: {len(session.sub_questions)}",
                f"- Sources collected: {len(ordered_sources)}",
                f"- Findings collected: {len(session.findings)}",
                f"- Claims generated: {len(session.claims)}",
                "- Retrieval policy: local corpus first, then public enrichment when local evidence is incomplete.",
                "- Local RAG note: uploaded and indexed local documents remain eligible even when external date filters are narrow, because local files may not carry reliable publication metadata.",
            ]
        )
        source_strategy = "\n".join(
            [
                f"- Local RAG enabled: {'yes' if SourceChannel.LOCAL_RAG in session.enabled_sources else 'no'}",
                f"- Web/Tavily enabled: {'yes' if SourceChannel.WEB in session.enabled_sources else 'no'}",
                f"- arXiv enabled: {'yes' if SourceChannel.ARXIV in session.enabled_sources else 'no'}",
                "- Local evidence is prioritized in both ranking and inline citation order.",
                "- External sources are ranked by relevance, credibility, metadata completeness, date-window fit, and corroboration.",
            ]
        )

        findings_by_question: dict[str, list[str]] = defaultdict(list)
        for finding in session.findings:
            linked_sources = [source_map[source_id] for source_id in finding.source_ids if source_id in source_map]
            citation = format_inline_citations(linked_sources[:4]) if linked_sources else "No citation available"
            snippet_line = f"  Snippet: {finding.quote_excerpt or finding.snippet}" if (finding.quote_excerpt or finding.snippet) else ""
            findings_by_question[finding.sub_question].append(
                f"- {finding.content}\n{snippet_line}\n  Citations: {citation}"
            )
        evidence_synthesis = "\n\n".join(
            f"### {question}\n" + "\n".join(entries[:5])
            for question, entries in findings_by_question.items()
        ) or "No evidence synthesis available."

        detailed_findings = "\n".join(
            f"- {claim.statement}\n"
            f"  Confidence: {claim.confidence.value} ({claim.confidence_pct}%), Trust: {claim.trust_score}%\n"
            f"  Credibility: {claim.credibility_summary}\n"
            f"  Evidence: {claim.evidence_summary}\n"
            f"  Citations: {format_inline_citations([source_map[source_id] for source_id in claim.supporting_source_ids if source_id in source_map][:4]) or 'No citation available'}"
            for claim in session.claims[:12]
        ) or "- No claims generated."

        contested = "\n".join(
            f"- {item.analysis}\n  Claim A: {item.claim_a}\n  Claim B: {item.claim_b}"
            for item in session.contradictions[:10]
        ) or "- No major contradictions detected."

        credibility_methodology = "\n".join(
            [
                "- Source credibility score is a weighted heuristic:",
                "  source-type weight (35%), provider trust (20%), metadata completeness (15%), date-window fit (15%), and cross-source agreement (15%).",
                "- Scores do not claim absolute truth; they communicate how strongly the retrieved evidence should be trusted relative to other collected material.",
                "",
                *[
                    f"- {(source.filename or source.title)} [{source.provider}] -> {source.credibility_score:.2f}. {source.credibility_explanation}"
                    for source in ordered_sources[:12]
                ],
            ]
        ) or "- No credibility data available."

        insights = "\n".join(
            f"- {insight.label}: {insight.content}\n  Evidence: {format_inline_citations([source_map[source_id] for source_id in insight.evidence_chain if source_id in source_map][:5]) or 'No citation available'}"
            for insight in session.insights[:10]
        ) or "- No insights generated."

        follow_ups = "\n".join(
            f"- {question.question}\n  Why it matters: {question.rationale}"
            for question in session.follow_up_questions[:8]
        ) or "- No follow-up questions."

        limitations = "\n".join(
            [
                "- Local documents may not always have reliable publication metadata, so date filtering is strongest for external web and arXiv sources.",
                "- Some web results may not expose publication dates; these are included with lower time-window certainty when otherwise relevant.",
                "- Findings without corroborating sources are retained but marked as lower-confidence evidence.",
            ]
        )

        rag_references = "\n".join(
            f"- {source.filename or source.title} | pages={','.join(str(page) for page in source.page_refs) if source.page_refs else 'n/a'} | snippet={source.snippet} | credibility={source.credibility_score:.2f}"
            for source in rag_sources[:30]
        ) or "- No local RAG references collected."

        reference_list = "\n".join(
            f"- {format_reference_entry(source)}"
            for source in ordered_sources[:50]
        ) or "- No sources collected."

        web_and_papers = "\n".join(
            f"- [{source.title}]({source.url}) | provider={source.provider} | type={source.source_type.value} | published={source.published_date or 'unknown'} | snippet={source.snippet}"
            for source in ordered_sources
            if source.url
        ) or "- No external links collected."

        session.report_sections = [
            ReportSection(section_type="summary", title="Executive Summary", content=f"{summary}\n\nPrimary citations: {format_inline_citations(ordered_sources[:8])}", order=1),
            ReportSection(section_type="methodology", title="Research Scope and Methodology", content=methodology, order=2),
            ReportSection(section_type="strategy", title="Source Strategy", content=source_strategy, order=3),
            ReportSection(section_type="evidence_synthesis", title="Evidence Synthesis by Sub-question", content=evidence_synthesis, order=4),
            ReportSection(section_type="findings", title="Detailed Findings", content=detailed_findings, order=5),
            ReportSection(section_type="contested", title="Contradictions and Disputed Claims", content=contested, order=6),
            ReportSection(section_type="credibility", title="Credibility and Trust Evaluation", content=credibility_methodology, order=7),
            ReportSection(section_type="insights", title="Insights and Interpretive Analysis", content=insights, order=8),
            ReportSection(section_type="limitations", title="Limitations and Open Questions", content=f"{limitations}\n\n{follow_ups}", order=9),
            ReportSection(section_type="links", title="Web and arXiv Links", content=web_and_papers, order=10),
            ReportSection(section_type="rag_refs", title="RAG Document References", content=rag_references, order=11),
            ReportSection(section_type="appendix", title="Comprehensive Bibliography / References", content=reference_list, order=12),
        ]
        return session
