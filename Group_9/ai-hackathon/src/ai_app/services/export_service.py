from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


class ExportService:
    def markdown_bytes(self, text: str) -> bytes:
        return text.encode("utf-8")

    def pdf_bytes(self, text: str) -> bytes:
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        text_obj = pdf.beginText(40, 750)
        for line in text.splitlines():
            text_obj.textLine(line[:110])
            if text_obj.getY() < 60:
                pdf.drawText(text_obj)
                pdf.showPage()
                text_obj = pdf.beginText(40, 750)
        pdf.drawText(text_obj)
        pdf.save()
        return buffer.getvalue()

