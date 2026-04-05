from __future__ import annotations

import re
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


class ExportService:
    def markdown_bytes(self, text: str) -> bytes:
        return text.encode("utf-8")

    def pdf_bytes(self, text: str) -> bytes:
        text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"[\1]", text)
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=0.7 * inch,
            rightMargin=0.7 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            spaceAfter=12,
        )
        heading_style = ParagraphStyle(
            "HeadingStyle",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            spaceBefore=10,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "BodyStyle",
            parent=styles["BodyText"],
            fontSize=10.5,
            leading=14,
            spaceAfter=6,
        )

        story = [Paragraph("AI Hackathon Deep Researcher Report", title_style), Spacer(1, 0.12 * inch)]
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                story.append(Spacer(1, 0.08 * inch))
                continue
            if line.startswith("## "):
                story.append(Paragraph(line[3:], heading_style))
                continue
            if line.startswith("### "):
                story.append(Paragraph(f"<b>{line[4:]}</b>", body_style))
                continue
            if line.startswith("- "):
                story.append(Paragraph(f"&bull; {line[2:]}", body_style))
                continue
            story.append(Paragraph(line, body_style))
        doc.build(story)
        return buffer.getvalue()
