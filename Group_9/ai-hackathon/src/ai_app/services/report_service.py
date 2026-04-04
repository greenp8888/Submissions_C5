from __future__ import annotations

from ai_app.schemas.research import ResearchSession


class ReportService:
    def render_markdown(self, session: ResearchSession) -> str:
        sections = sorted(session.report_sections, key=lambda section: section.order)
        return "\n\n".join(f"## {section.title}\n\n{section.content}" for section in sections)

