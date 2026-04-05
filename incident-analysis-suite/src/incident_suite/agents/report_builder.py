from __future__ import annotations

import re

from incident_suite.agents.common import with_stage
from incident_suite.models.state import IncidentState


def build_salesforce_class_mermaid(class_name: str, class_body: str) -> str:
    method_names = []
    for match in re.finditer(r"(?:public|private|protected|global)\s+(?:static\s+)?[\w<>,]+\s+(\w+)\s*\(", class_body):
        method_names.append(match.group(1))
    if not method_names:
        method_names = ["execute"]
    method_lines = "\n".join(f"        +{method}()" for method in method_names[:10])
    return (
        "classDiagram\n"
        f'    class {class_name} {{\n'
        f"{method_lines}\n"
        "    }\n"
    )


def report_builder_node(state: IncidentState) -> IncidentState:
    issue_lines = "\n".join(f"- {issue.title}: {issue.probable_root_cause}" for issue in state.get("detected_issues", [])) or "- No issues detected"
    evidence_lines = "\n".join(f"- {item.claim} (verified={item.verified}, confidence={item.confidence:.2f})" for item in state.get("evidence_items", [])) or "- No evidence items"
    remediation_lines = "\n".join(f"- {rem.fix}" for rem in state.get("remediations", [])) or "- No remediations"
    report_markdown = (
        f"# Incident Report\n\n"
        f"## Severity\n{state.get('severity', 'unknown')}\n\n"
        f"## Findings\n{issue_lines}\n\n"
        f"## Evidence\n{evidence_lines}\n\n"
        f"## Recommended Actions\n{remediation_lines}\n"
    )
    salesforce_class_name = state.get("salesforce_class_name", "") or "SalesforceClass"
    salesforce_class_body = state.get("salesforce_class_body", "") or ""
    if salesforce_class_body.strip():
        mermaid_diagram = build_salesforce_class_mermaid(salesforce_class_name, salesforce_class_body)
    else:
        mermaid_diagram = (
            "flowchart LR\n"
            '    Logs["Logs + Source Docs"] --> Planner["Planner"]\n'
            '    Planner --> Retriever["Retriever + LanceDB"]\n'
            '    Retriever --> Evidence["Evidence + Verification"]\n'
            '    Evidence --> Fix["Code Generator"]\n'
            '    Fix --> Report["Report + Export"]\n'
        )
    return with_stage(state, "report_builder", "completed", "Report builder assembled the final markdown report and Mermaid architecture snippet.", report_markdown=report_markdown, mermaid_diagram=mermaid_diagram, status="report_ready")
