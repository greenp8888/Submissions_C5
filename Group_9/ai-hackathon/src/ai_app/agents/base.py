from __future__ import annotations

from ai_app.schemas.research import AgentTraceEntry, ResearchEvent, ResearchSession


class AgentBase:
    name = "agent"

    async def emit(self, session: ResearchSession, message: str, event_type: str = "status") -> ResearchEvent:
        return ResearchEvent(event_type=event_type, agent=self.name, message=message)

    def trace(self, step: str, input_summary: str = "", output_summary: str = "", token_estimate: int = 0) -> AgentTraceEntry:
        return AgentTraceEntry(
            agent=self.name,
            step=step,
            input_summary=input_summary,
            output_summary=output_summary,
            token_estimate=token_estimate,
        )

