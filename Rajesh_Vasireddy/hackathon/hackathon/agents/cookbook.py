"""Cookbook Agent – converts a RemediationPlan into a runbook markdown checklist."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from .base_agent import BaseAgent
from .remediation import RemediationPlan

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a technical writer who specialises in SRE runbooks.

Given a structured remediation plan, produce a clean, well-formatted Markdown
runbook/checklist that an on-call engineer can follow step-by-step. Include:

- A header with incident type, severity, and generation timestamp.
- A "Quick Reference" summary box (≤ 5 bullet points).
- Numbered checklist steps with sub-bullets for commands (use code blocks).
- A "Rollback" section.
- A "Prevention" section.

Write directly in Markdown. No JSON, no preamble outside the document.
"""


class CookbookAgent(BaseAgent):
    """
    Converts a :class:`~agents.remediation.RemediationPlan` into a Markdown runbook.

    The generated runbook includes a header, quick-reference summary, numbered
    checklist with shell commands, rollback instructions, and prevention notes.
    It is stored in ``IncidentState.cookbook_md`` and made available for
    download in the UI and as an excerpt in JIRA / Slack notifications.
    """

    system_prompt = SYSTEM_PROMPT
    max_tokens = 4096

    def run(self, plan: RemediationPlan) -> str:  # type: ignore[override]
        """
        Generate a Markdown runbook from *plan* and return it as a string.

        Parameters
        ----------
        plan:
            The structured remediation plan produced by
            :class:`~agents.remediation.RemediationAgent`.

        Returns
        -------
        str
            A complete Markdown document suitable for saving or rendering in
            the UI.
        """
        steps_text = "\n".join(
            f"{s.order}. [{s.owner}] {s.action} (~{s.estimated_minutes} min)\n"
            f"   Command: `{s.command}`\n"
            f"   Rationale: {s.rationale}"
            for s in plan.steps
        )

        prompt = (
            f"Incident type : {plan.incident_type}\n"
            f"Severity      : {plan.severity}\n"
            f"Timestamp     : {datetime.now(timezone.utc).isoformat()}\n\n"
            f"Remediation steps:\n{steps_text}\n\n"
            f"Rollback plan : {plan.rollback_plan}\n"
            f"Prevention    : {plan.prevention_notes}\n\n"
            "Generate the runbook now."
        )
        return self._call(prompt)
