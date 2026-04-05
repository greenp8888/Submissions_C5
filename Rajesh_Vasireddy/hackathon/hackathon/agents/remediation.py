"""Remediation Agent – converts a LogReport into a RemediationPlan."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import List

from .base_agent import BaseAgent, extract_json_payload
from .log_classifier import LogReport

logger = logging.getLogger(__name__)


@dataclass
class RemediationStep:
    order: int
    action: str
    command: str = ""
    rationale: str = ""
    owner: str = "SRE"
    estimated_minutes: int = 5


@dataclass
class RemediationPlan:
    incident_type: str
    severity: str
    steps: List[RemediationStep] = field(default_factory=list)
    rollback_plan: str = ""
    prevention_notes: str = ""


SYSTEM_PROMPT = """\
You are a principal SRE responsible for incident remediation playbooks.

Given a structured incident report you must produce a concrete, step-by-step
remediation plan that an on-call engineer can execute immediately.

Return ONLY valid JSON with this structure:
{
  "steps": [
    {
      "order": 1,
      "action": "Short imperative description",
      "command": "kubectl … (or empty string)",
      "rationale": "Why this step matters",
      "owner": "SRE | DBA | NetOps | etc.",
      "estimated_minutes": 5
    }
  ],
  "rollback_plan": "How to safely roll back if remediation worsens the situation.",
  "prevention_notes": "Long-term prevention recommendation."
}
No markdown fences, no extra text.
"""


class RemediationAgent(BaseAgent):
    system_prompt = SYSTEM_PROMPT
    max_tokens = 3072

    def run(self, report: LogReport) -> RemediationPlan:  # type: ignore[override]
        prompt = (
            f"Incident type : {report.incident_type}\n"
            f"Severity      : {report.severity}\n"
            f"Root cause    : {report.root_cause}\n"
            f"Services      : {', '.join(report.affected_services)}\n"
            f"Error patterns: {'; '.join(report.error_patterns)}\n\n"
            "Produce the remediation plan now."
        )
        raw = self._call(prompt)

        try:
            raw = extract_json_payload(raw)
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("Remediation JSON parse error: %s\nRaw: %s", exc, raw)
            raise ValueError("RemediationAgent returned non-JSON output.") from exc

        steps = [
            RemediationStep(
                order=s.get("order", i + 1),
                action=s.get("action", ""),
                command=s.get("command", ""),
                rationale=s.get("rationale", ""),
                owner=s.get("owner", "SRE"),
                estimated_minutes=int(s.get("estimated_minutes", 5)),
            )
            for i, s in enumerate(data.get("steps", []))
        ]

        return RemediationPlan(
            incident_type=report.incident_type,
            severity=report.severity,
            steps=steps,
            rollback_plan=data.get("rollback_plan", ""),
            prevention_notes=data.get("prevention_notes", ""),
        )
