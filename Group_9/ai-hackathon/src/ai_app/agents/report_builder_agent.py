from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime

from ai_app.agents.base import AgentBase
from ai_app.domain.enums import SourceChannel
from ai_app.retrieval.citation_builder import (
    build_reference_index,
    format_inline_citations,
    format_reference_link,
    order_sources_for_citation,
    sanitize_report_text,
)
from ai_app.retrieval.time_filters import describe_date_window
from ai_app.schemas.research import (
    ReportBlock,
    ReportCitation,
    ReportMetaItem,
    ReportSection,
    ReportVisual,
    ReportVisualPoint,
    ResearchSession,
    Source,
)


class ReportBuilderAgent(AgentBase):
    name = "report_builder_agent"

    async def run(self, session: ResearchSession) -> ResearchSession:
        ordered_sources = order_sources_for_citation(session.sources)
        reference_index = build_reference_index(ordered_sources)
        source_map = {source.id: source for source in ordered_sources}
        rag_sources = [source for source in ordered_sources if source.provider == "local_rag"]
        contested_claims = [claim for claim in session.claims if claim.contested or claim.consensus_pct < 60]
        enabled_sources = ", ".join(source.value for source in session.enabled_sources)
        date_window = describe_date_window(session.start_date, session.end_date)
        quantitative_visual = self._extract_quantitative_visual(ordered_sources)
        limits = self._section_limits(session)

        report_sections: list[ReportSection] = [
            ReportSection(
                section_type="summary",
                title="Executive Summary",
                lead_summary=sanitize_report_text(session.claims[0].statement) if session.claims else "Research session completed with limited evidence.",
                blocks=[
                    ReportBlock(
                        title="Primary grounding",
                        summary="This summary is grounded in the highest-ranked evidence collected during the run.",
                        citations=self._citations_for_sources(ordered_sources[:8], reference_index),
                        metadata=[
                            ReportMetaItem(label="Sources reviewed", value=str(len(ordered_sources))),
                            ReportMetaItem(label="Claims generated", value=str(len(session.claims))),
                        ],
                    )
                ],
                order=1,
            ),
            ReportSection(
                section_type="methodology",
                title="Research Scope and Methodology",
                lead_summary=f"Question: {sanitize_report_text(session.query)}",
                blocks=[
                    ReportBlock(
                        summary="The investigation used a local-first retrieval policy and only expanded into public sources when local evidence was incomplete.",
                        narrative="The workflow captured planning, retrieval, analysis, contradiction detection, insight generation, and reporting in sequence.",
                        metadata=[
                            ReportMetaItem(label="Run mode", value=self._humanize_value(session.run_mode.value)),
                            ReportMetaItem(label="Depth", value=self._humanize_value(session.depth.value)),
                            ReportMetaItem(label="Enabled sources", value=enabled_sources),
                            ReportMetaItem(label="Date window", value=date_window),
                            ReportMetaItem(label="Sub-questions", value=str(len(session.sub_questions))),
                        ],
                    ),
                    ReportBlock(
                        summary="Local documents remain eligible even when external date filters are narrow, because local files may not carry reliable publication metadata.",
                    ),
                ],
                order=2,
            ),
            ReportSection(
                section_type="strategy",
                title="Source Strategy",
                lead_summary="Evidence priority was local documents first, then web and arXiv enrichment based on relevance, credibility, metadata quality, time-window fit, and corroboration.",
                blocks=[
                    ReportBlock(
                        summary="Source coverage for this run.",
                        metadata=[
                            ReportMetaItem(label="Local RAG", value="Enabled" if SourceChannel.LOCAL_RAG in session.enabled_sources else "Disabled"),
                            ReportMetaItem(label="Web and Tavily", value="Enabled" if SourceChannel.WEB in session.enabled_sources else "Disabled"),
                            ReportMetaItem(label="arXiv", value="Enabled" if SourceChannel.ARXIV in session.enabled_sources else "Disabled"),
                        ],
                    )
                ],
                order=3,
            ),
            ReportSection(
                section_type="evidence_synthesis",
                title="Evidence Synthesis by Sub-question",
                lead_summary="The evidence below is organized by the sub-questions investigated during the run.",
                blocks=self._build_evidence_blocks(session, source_map, reference_index, limits["findings"]),
                order=4,
            ),
            ReportSection(
                section_type="findings",
                title="Detailed Findings",
                lead_summary="Each finding below starts with the main takeaway, followed by compact evidence, citations, and trust signals.",
                blocks=self._build_claim_blocks(session, source_map, reference_index, limits["claims"]),
                visual=quantitative_visual,
                order=5,
            ),
        ]

        next_order = 6
        if session.debate_mode or session.contradictions or contested_claims:
            report_sections.append(
                ReportSection(
                    section_type="comparative_analysis",
                    title="Comparative Analysis",
                    lead_summary=self._build_comparative_lead(session),
                    blocks=self._build_comparative_blocks(session, source_map, reference_index, limits["contradictions"]),
                    order=next_order,
                )
            )
            next_order += 1

        if session.contradictions:
            report_sections.append(
                ReportSection(
                    section_type="contested",
                    title="Contradictions and Disputed Claims",
                    lead_summary="The following items show where retrieved sources disagreed and how the system weighted the evidence.",
                    blocks=self._build_contradiction_blocks(session, reference_index, limits["contradictions"]),
                    order=next_order,
                )
            )
            next_order += 1

        if contested_claims:
            report_sections.append(
                ReportSection(
                    section_type="contested_claims",
                    title="Contested Claims (Low Consensus)",
                    lead_summary="These claims showed lower consensus or stronger contradiction pressure across the evidence base.",
                    blocks=self._build_contested_claim_blocks(contested_claims, source_map, reference_index, limits["contested_claims"]),
                    order=next_order,
                )
            )
            next_order += 1

        report_sections.extend(
            [
                ReportSection(
                    section_type="credibility",
                    title="Credibility and Trust Evaluation",
                    lead_summary="Confidence and trust score are different signals: confidence reflects claim-level certainty, while trust score reflects the quality of the supporting evidence base.",
                    blocks=self._build_credibility_blocks(ordered_sources, reference_index, limits["sources"]),
                    footer_notes=[
                        "Source credibility heuristic weights source type at 35%, provider trust at 20%, metadata completeness at 15%, date-window fit at 15%, and cross-source agreement at 15%.",
                        "Confidence reflects support, contradiction, agreement, and evidence sufficiency.",
                        "Trust score reflects source quality, provider quality, metadata completeness, date fit, and corroboration.",
                        *[note for note in session.metadata.get("provider_warnings", []) if isinstance(note, str)],
                    ],
                    order=next_order,
                ),
                ReportSection(
                    section_type="insights",
                    title="Insights and Interpretive Analysis",
                    lead_summary="These insights synthesize patterns across findings rather than simply repeating a single source.",
                    blocks=self._build_insight_blocks(session, source_map, reference_index, limits["insights"]),
                    order=next_order + 1,
                ),
                ReportSection(
                    section_type="limitations",
                    title="Limitations and Open Questions",
                    lead_summary="The following limitations and follow-up questions identify where evidence remained thin, dated, or contested.",
                    blocks=self._build_limitations_blocks(session),
                    order=next_order + 2,
                ),
                ReportSection(
                    section_type="links",
                    title="Web and arXiv Links",
                    lead_summary="External sources are listed below with their main summary first and compact metadata after.",
                    blocks=self._build_link_blocks([source for source in ordered_sources if source.url], reference_index, limits["external_links"]),
                    order=next_order + 3,
                ),
                ReportSection(
                    section_type="rag_refs",
                    title="RAG Document References",
                    lead_summary="Local RAG references include the supporting summary first, followed by compact file, page, and credibility details.",
                    blocks=self._build_reference_blocks(rag_sources, reference_index, limits["rag_refs"]),
                    order=next_order + 4,
                ),
                ReportSection(
                    section_type="appendix",
                    title="Comprehensive Bibliography / References",
                    lead_summary="All ranked sources used in this run are listed below in a humanized reference format.",
                    blocks=self._build_reference_blocks(ordered_sources, reference_index, limits["sources"]),
                    order=next_order + 5,
                ),
            ]
        )
        session.report_sections = report_sections
        return session

    def _build_evidence_blocks(self, session: ResearchSession, source_map: dict[str, Source], reference_index: dict[str, int], limit: int) -> list[ReportBlock]:
        findings_by_question: dict[str, list[ReportBlock]] = defaultdict(list)
        for finding in session.findings[:limit]:
            linked_sources = [source_map[source_id] for source_id in finding.source_ids if source_id in source_map]
            findings_by_question[self._humanize_text(finding.sub_question)].append(
                ReportBlock(
                    summary=sanitize_report_text(finding.quote_excerpt or finding.snippet or finding.content),
                    narrative=sanitize_report_text(finding.content),
                    citations=self._citations_for_sources(linked_sources[:4], reference_index),
                    metadata=self._source_footer_metadata(linked_sources[:2]),
                )
            )
        blocks: list[ReportBlock] = []
        for question, entries in findings_by_question.items():
            blocks.append(
                ReportBlock(
                    title=question,
                    summary=f"{len(entries)} evidence item(s) supported this sub-question.",
                )
            )
            blocks.extend(entries[: max(5, limit // max(1, len(findings_by_question)))])
        return blocks or [ReportBlock(summary="No evidence synthesis was generated for this run.")]

    def _build_claim_blocks(self, session: ResearchSession, source_map: dict[str, Source], reference_index: dict[str, int], limit: int) -> list[ReportBlock]:
        blocks: list[ReportBlock] = []
        for claim in session.claims[:limit]:
            sources = [source_map[source_id] for source_id in claim.supporting_source_ids if source_id in source_map]
            blocks.append(
                ReportBlock(
                    title=self._humanize_claim_side(claim.debate_position),
                    summary=sanitize_report_text(claim.statement),
                    narrative=sanitize_report_text(claim.evidence_summary),
                    citations=self._citations_for_sources(sources[:4], reference_index),
                    metadata=[
                        ReportMetaItem(label="Confidence", value=f"{self._humanize_value(claim.confidence.value)} ({claim.confidence_pct}%)"),
                        ReportMetaItem(label="Trust score", value=f"{claim.trust_score}%"),
                        ReportMetaItem(label="Consensus", value=f"{claim.consensus_pct}%"),
                        ReportMetaItem(label="Credibility note", value=sanitize_report_text(claim.credibility_summary)),
                    ],
                )
            )
        return blocks or [ReportBlock(summary="No claims were generated for this run.")]

    def _build_contradiction_blocks(self, session: ResearchSession, reference_index: dict[str, int], limit: int) -> list[ReportBlock]:
        blocks: list[ReportBlock] = []
        for contradiction in session.contradictions[:limit]:
            citations = []
            for source_id in (contradiction.source_a_id, contradiction.source_b_id):
                if not source_id or source_id not in reference_index:
                    continue
                citations.append(ReportCitation(source_id=source_id, label=f"[{reference_index[source_id]}]"))
            blocks.append(
                ReportBlock(
                    title="Cross-source disagreement",
                    summary=sanitize_report_text(contradiction.analysis),
                    narrative=(
                        f"Source A says: {sanitize_report_text(contradiction.claim_a)}. "
                        f"Source B says: {sanitize_report_text(contradiction.claim_b)}."
                    ),
                    citations=citations,
                    metadata=[
                        ReportMetaItem(label="Source A", value=self._humanize_text(contradiction.source_a_label or "Unknown source")),
                        ReportMetaItem(label="Source B", value=self._humanize_text(contradiction.source_b_label or "Unknown source")),
                        ReportMetaItem(label="Weighted lean", value=self._humanize_value(contradiction.credibility_lean or "mixed")),
                        ReportMetaItem(label="Why", value=sanitize_report_text(contradiction.weighting_rationale or contradiction.resolution or "Comparable support across conflicting evidence.")),
                    ],
                )
            )
        return blocks

    def _build_contested_claim_blocks(self, claims, source_map: dict[str, Source], reference_index: dict[str, int], limit: int) -> list[ReportBlock]:
        blocks: list[ReportBlock] = []
        for claim in claims[:limit]:
            sources = [source_map[source_id] for source_id in claim.supporting_source_ids if source_id in source_map]
            blocks.append(
                ReportBlock(
                    summary=sanitize_report_text(claim.statement),
                    narrative=sanitize_report_text(claim.evidence_summary),
                    citations=self._citations_for_sources(sources[:4], reference_index),
                    metadata=[
                        ReportMetaItem(label="Consensus", value=f"{claim.consensus_pct}%"),
                        ReportMetaItem(label="Confidence", value=f"{self._humanize_value(claim.confidence.value)} ({claim.confidence_pct}%)"),
                        ReportMetaItem(label="Trust score", value=f"{claim.trust_score}%"),
                    ],
                )
            )
        return blocks

    def _build_credibility_blocks(self, sources: list[Source], reference_index: dict[str, int], limit: int) -> list[ReportBlock]:
        blocks: list[ReportBlock] = [
            ReportBlock(
                summary="Confidence answers how sure the system is about a claim. Trust score answers how trustworthy the supporting evidence base is.",
                narrative="A claim can show high confidence from consistent evidence but only moderate trust if the sources are weak. It can also have strong-trust sources but lower confidence if those sources disagree.",
            )
        ]
        for source in sources[:limit]:
            blocks.append(
                ReportBlock(
                    title=self._display_source_title(source),
                    summary=sanitize_report_text(source.snippet or source.title),
                    citations=self._citations_for_sources([source], reference_index),
                    metadata=[
                        ReportMetaItem(label="Provider", value=self._humanize_value(source.provider)),
                        ReportMetaItem(label="Source type", value=self._humanize_value(source.source_type.value)),
                        ReportMetaItem(label="Credibility", value=f"{source.credibility_score:.2f}"),
                        ReportMetaItem(label="Relevance", value=f"{source.relevance_score:.2f}"),
                        ReportMetaItem(label="Published", value=source.published_date or "Unknown"),
                        ReportMetaItem(label="Rationale", value=sanitize_report_text(source.credibility_explanation)),
                    ],
                )
            )
        return blocks

    def _build_insight_blocks(self, session: ResearchSession, source_map: dict[str, Source], reference_index: dict[str, int], limit: int) -> list[ReportBlock]:
        blocks: list[ReportBlock] = []
        for insight in session.insights[:limit]:
            sources = [source_map[source_id] for source_id in insight.evidence_chain if source_id in source_map]
            blocks.append(
                ReportBlock(
                    title=self._humanize_text(insight.label),
                    summary=sanitize_report_text(insight.content),
                    citations=self._citations_for_sources(sources[:5], reference_index),
                    metadata=[ReportMetaItem(label="Insight type", value=self._humanize_value(insight.insight_type.value if hasattr(insight.insight_type, "value") else str(insight.insight_type)))],
                )
            )
        return blocks or [ReportBlock(summary="No higher-order insights were generated for this run.")]

    def _build_limitations_blocks(self, session: ResearchSession) -> list[ReportBlock]:
        blocks = [
            ReportBlock(summary="Local documents may not always have reliable publication metadata, so date filtering is strongest for external web and arXiv sources."),
            ReportBlock(summary="Some web results may not expose publication dates; these are included with lower time-window certainty when otherwise relevant."),
            ReportBlock(summary="Findings without corroborating sources are retained but marked as lower-confidence evidence."),
        ]
        for question in session.follow_up_questions[:8]:
            blocks.append(
                ReportBlock(
                    title="Follow-up question",
                    summary=sanitize_report_text(question.question),
                    narrative=sanitize_report_text(question.rationale),
                )
            )
        return blocks

    def _build_link_blocks(self, sources: list[Source], reference_index: dict[str, int], limit: int) -> list[ReportBlock]:
        blocks: list[ReportBlock] = []
        for source in sources[:limit]:
            blocks.append(
                ReportBlock(
                    title=self._display_source_title(source),
                    summary=sanitize_report_text(source.snippet or source.title),
                    citations=self._citations_for_sources([source], reference_index),
                    metadata=self._reference_metadata(source),
                )
            )
        return blocks or [ReportBlock(summary="No external links were collected.")]

    def _build_reference_blocks(self, sources: list[Source], reference_index: dict[str, int], limit: int) -> list[ReportBlock]:
        blocks: list[ReportBlock] = []
        for source in sources[:limit]:
            blocks.append(
                ReportBlock(
                    title=self._display_source_title(source),
                    summary=sanitize_report_text(source.snippet or source.title),
                    citations=self._citations_for_sources([source], reference_index),
                    metadata=self._reference_metadata(source),
                )
            )
        return blocks or [ReportBlock(summary="No sources were collected.")]

    def _build_comparative_lead(self, session: ResearchSession) -> str:
        if session.debate_mode and session.position_a and session.position_b:
            return (
                f"Debate mode compared Position A, {sanitize_report_text(session.position_a)}, "
                f"against Position B, {sanitize_report_text(session.position_b)}, using the same citation and credibility mechanics as the rest of the report."
            )
        if session.contradictions:
            return "Comparative analysis was generated from cross-source disagreement rather than an explicit debate setup."
        return "No meaningful comparative analysis was required for this run."

    def _build_comparative_blocks(self, session: ResearchSession, source_map: dict[str, Source], reference_index: dict[str, int], limit: int) -> list[ReportBlock]:
        blocks: list[ReportBlock] = []
        if session.debate_mode and session.position_a and session.position_b:
            a_claims = [claim for claim in session.claims if claim.debate_position == "position_a"]
            b_claims = [claim for claim in session.claims if claim.debate_position == "position_b"]
            a_support = round(sum(claim.trust_score for claim in a_claims) / max(1, len(a_claims))) if a_claims else 0
            b_support = round(sum(claim.trust_score for claim in b_claims) / max(1, len(b_claims))) if b_claims else 0
            verdict = session.position_a if a_support > b_support else session.position_b if b_support > a_support else "Mixed"
            blocks.append(
                ReportBlock(
                    title="Weight of evidence",
                    summary=f"The current evidence leans toward {sanitize_report_text(verdict)}.",
                    metadata=[
                        ReportMetaItem(label="Position A average trust", value=f"{a_support}%"),
                        ReportMetaItem(label="Position B average trust", value=f"{b_support}%"),
                        ReportMetaItem(label="Position A claims", value=str(len(a_claims))),
                        ReportMetaItem(label="Position B claims", value=str(len(b_claims))),
                    ],
                )
            )
        for contradiction in session.contradictions[:limit]:
            related_sources = [source_map[source_id] for source_id in (contradiction.source_a_id, contradiction.source_b_id) if source_id in source_map]
            blocks.append(
                ReportBlock(
                    summary=sanitize_report_text(contradiction.analysis),
                    narrative=f"{sanitize_report_text(contradiction.claim_a)} contrasted with {sanitize_report_text(contradiction.claim_b)}.",
                    citations=self._citations_for_sources(related_sources, reference_index),
                    metadata=[
                        ReportMetaItem(label="Weighted lean", value=self._humanize_value(contradiction.credibility_lean or "mixed")),
                        ReportMetaItem(label="Reason", value=sanitize_report_text(contradiction.weighting_rationale or "Comparable support across conflicting evidence.")),
                    ],
                )
            )
        return blocks or [ReportBlock(summary="No comparative evidence required additional interpretation.")]

    def _section_limits(self, session: ResearchSession) -> dict[str, int]:
        if session.depth.value == "deep":
            return {
                "findings": 72,
                "claims": 28,
                "contradictions": 18,
                "contested_claims": 18,
                "sources": 100,
                "insights": 18,
                "external_links": 60,
                "rag_refs": 60,
            }
        if session.depth.value == "standard":
            return {
                "findings": 40,
                "claims": 16,
                "contradictions": 10,
                "contested_claims": 10,
                "sources": 60,
                "insights": 12,
                "external_links": 36,
                "rag_refs": 36,
            }
        return {
            "findings": 18,
            "claims": 8,
            "contradictions": 6,
            "contested_claims": 6,
            "sources": 30,
            "insights": 8,
            "external_links": 20,
            "rag_refs": 20,
        }

    def _extract_quantitative_visual(self, sources: list[Source]) -> ReportVisual | None:
        ranked_sources = sorted(
            sources,
            key=lambda source: (source.credibility_score, self._published_timestamp(source.published_date), source.relevance_score),
            reverse=True,
        )
        for source in ranked_sources:
            points = self._extract_year_value_points(source.snippet)
            if len(points) < 2:
                continue
            return ReportVisual(
                chart_type="line",
                title=f"Quantitative trend from {self._display_source_title(source)}",
                description="Chart generated only because the source snippet exposed explicit year-value pairs.",
                unit="",
                source_ids=[source.id],
                points=points,
            )
        return None

    def _extract_year_value_points(self, text: str) -> list[ReportVisualPoint]:
        cleaned = sanitize_report_text(text)
        patterns = [
            re.finditer(r"(?P<label>20\d{2})\s*[:=,-]?\s*(?P<value>\d+(?:\.\d+)?)", cleaned),
            re.finditer(r"(?P<value>\d+(?:\.\d+)?)\s*(?:in|for|during)\s*(?P<label>20\d{2})", cleaned),
        ]
        seen: set[str] = set()
        points: list[ReportVisualPoint] = []
        for iterator in patterns:
            for match in iterator:
                label = match.group("label")
                if label in seen:
                    continue
                seen.add(label)
                points.append(ReportVisualPoint(label=label, value=float(match.group("value"))))
        return sorted(points, key=lambda point: point.label)

    def _published_timestamp(self, published_date: str | None) -> float:
        if not published_date:
            return 0.0
        try:
            return datetime.fromisoformat(published_date.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return 0.0

    def _citations_for_sources(self, sources: list[Source], reference_index: dict[str, int]) -> list[ReportCitation]:
        citations: list[ReportCitation] = []
        for source in sources:
            if source.id not in reference_index:
                continue
            citations.append(
                ReportCitation(
                    source_id=source.id,
                    label=f"[{reference_index[source.id]}]",
                    title=self._display_source_title(source),
                    url=source.url,
                )
            )
        return citations

    def _reference_metadata(self, source: Source) -> list[ReportMetaItem]:
        metadata = [
            ReportMetaItem(label="Provider", value=self._humanize_value(source.provider)),
            ReportMetaItem(label="Source type", value=self._humanize_value(source.source_type.value)),
            ReportMetaItem(label="Credibility", value=f"{source.credibility_score:.2f}"),
            ReportMetaItem(label="Relevance", value=f"{source.relevance_score:.2f}"),
        ]
        if source.published_date:
            metadata.append(ReportMetaItem(label="Published", value=source.published_date))
        if source.page_refs:
            metadata.append(ReportMetaItem(label="Pages", value=", ".join(str(page) for page in source.page_refs)))
        if source.filename:
            metadata.append(ReportMetaItem(label="File", value=source.filename))
        if source.credibility_explanation:
            metadata.append(ReportMetaItem(label="Credibility rationale", value=sanitize_report_text(source.credibility_explanation)))
        return metadata

    def _source_footer_metadata(self, sources: list[Source]) -> list[ReportMetaItem]:
        metadata: list[ReportMetaItem] = []
        for source in sources:
            metadata.append(
                ReportMetaItem(
                    label=self._display_source_title(source),
                    value=f"{self._humanize_value(source.provider)}, credibility {source.credibility_score:.2f}",
                )
            )
        return metadata

    def _display_source_title(self, source: Source) -> str:
        return self._humanize_text(source.filename or source.title)

    def _humanize_claim_side(self, position: str) -> str:
        if position == "position_a":
            return "Position A"
        if position == "position_b":
            return "Position B"
        return "Finding"

    def _humanize_value(self, value: str) -> str:
        normalized = self._humanize_text(value)
        if normalized.lower() == "mixed":
            return "Mixed"
        return normalized

    def _humanize_text(self, text: str) -> str:
        sanitized = sanitize_report_text(text).replace("_", " ").replace("—", "-").replace("–", "-")
        return " ".join(sanitized.split())
