from __future__ import annotations

from incident_suite.agents.common import with_stage
from incident_suite.models.schemas import ExportArtifact
from incident_suite.models.state import IncidentState


def export_agent_node(state: IncidentState) -> IncidentState:
    artifacts = [
        ExportArtifact(name="incident-report.md", kind="markdown", content=state.get("report_markdown", "")),
        ExportArtifact(name="incident-diagram.mmd", kind="mermaid", content=state.get("mermaid_diagram", "")),
    ]
    return with_stage(state, "export_agent", "completed", "Export agent packaged markdown and Mermaid outputs for download.", export_artifacts=artifacts, status="complete")
