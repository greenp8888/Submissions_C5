from __future__ import annotations

from ai_app.schemas.research import ReportSection, ResearchSession


class ReportService:
    def render_markdown(self, session: ResearchSession) -> str:
        sections = sorted(session.report_sections, key=lambda section: section.order)
        return "\n\n".join(self._render_section(section) for section in sections)

    def _render_section(self, section: ReportSection) -> str:
        lines = [f"## {section.title}"]
        if section.lead_summary:
            lines.append(section.lead_summary)
        elif section.content:
            lines.append(section.content)

        for block in section.blocks:
            if block.title:
                lines.append(f"### {block.title}")
            if block.summary:
                lines.append(block.summary)
            if block.narrative:
                lines.append(block.narrative)
            if block.citations:
                lines.append(
                    "References: "
                    + ", ".join(
                        citation.label if not citation.url else f"{citation.label} ({citation.title or citation.url})"
                        for citation in block.citations
                    )
                )
            if block.metadata:
                lines.append(
                    "Metadata: "
                    + " | ".join(f"{item.label}: {item.value}" for item in block.metadata)
                )
            if block.visual and block.visual.points:
                lines.append(f"Quantitative visual: {block.visual.title}")
                for point in block.visual.points:
                    lines.append(f"- {point.label}: {point.value:g}{block.visual.unit}")

        if section.visual and section.visual.points:
            lines.append(f"### {section.visual.title}")
            if section.visual.description:
                lines.append(section.visual.description)
            for point in section.visual.points:
                lines.append(f"- {point.label}: {point.value:g}{section.visual.unit}")

        if section.footer_notes:
            lines.append("Notes:")
            lines.extend(f"- {note}" for note in section.footer_notes)
        return "\n\n".join(line for line in lines if line)
