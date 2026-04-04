from __future__ import annotations

from pydantic import BaseModel, Field

from ai_app.schemas.research import ReportSection


class ReportResponse(BaseModel):
    sections: list[ReportSection] = Field(default_factory=list)

