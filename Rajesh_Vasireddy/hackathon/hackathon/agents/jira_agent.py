"""JIRA Agent – creates a JIRA ticket for CRITICAL incidents."""

from __future__ import annotations

import logging
import os
from typing import Optional

from .base_agent import BaseAgent
from .log_classifier import LogReport
from .remediation import RemediationPlan

logger = logging.getLogger(__name__)


class JiraAgent(BaseAgent):
    """
    Creates a JIRA ticket for CRITICAL incidents only.

    Uses the JIRA REST API v3 via :class:`~integrations.jira_client.JiraClient`.
    The ticket description is built from the log report, remediation steps, and
    the first 2 000 characters of the runbook.

    Requires ``JIRA_URL``, ``JIRA_USER``, and ``JIRA_API_TOKEN`` environment
    variables.  ``JIRA_PROJECT_KEY`` defaults to ``"OPS"`` when omitted.
    """

    def run(  # type: ignore[override]
        self,
        report: LogReport,
        plan: Optional[RemediationPlan] = None,
        cookbook_md: str = "",
    ) -> Optional[str]:
        """
        Create a JIRA ticket for the incident if severity is CRITICAL.

        Parameters
        ----------
        report:
            Classified incident report.
        plan:
            Optional remediation plan; its steps are included in the ticket
            description when provided.
        cookbook_md:
            Optional runbook markdown; an excerpt is appended to the description.

        Returns
        -------
        str or None
            The JIRA ticket key (e.g. ``"OPS-42"``) on success, or ``None``
            when the incident is not CRITICAL, credentials are missing, or
            ticket creation fails.
        """
        if report.severity != "CRITICAL":
            logger.info("Severity %s – JIRA ticket not required.", report.severity)
            return None

        jira_url = os.getenv("JIRA_URL", "")
        jira_user = os.getenv("JIRA_USER", "")
        jira_token = os.getenv("JIRA_API_TOKEN", "")
        jira_project = os.getenv("JIRA_PROJECT_KEY", "OPS")

        if not all([jira_url, jira_user, jira_token]):
            logger.warning("JIRA credentials not fully configured – skipping ticket creation.")
            return None

        from integrations.jira_client import JiraClient  # lazy import

        client = JiraClient(url=jira_url, user=jira_user, token=jira_token)

        summary = f"[CRITICAL] {report.incident_type} – {', '.join(report.affected_services[:3])}"
        description = self._build_description(report, plan, cookbook_md)

        ticket_key = client.create_issue(
            project=jira_project,
            summary=summary,
            description=description,
            priority="High",
            issue_type="Task",
            labels=["auto-incident", report.severity.lower(), report.incident_type.lower().replace(" ", "-")],
        )
        if ticket_key:
            logger.info("JIRA ticket created: %s", ticket_key)
        return ticket_key

    # ------------------------------------------------------------------

    @staticmethod
    def _build_description(
        report: LogReport,
        plan: Optional[RemediationPlan],
        cookbook_md: str,
    ) -> str:
        """
        Assemble the plain-text JIRA ticket description.

        Combines severity metadata, executive summary, up to 10 remediation
        steps, and a runbook excerpt (first 2 000 characters).
        """
        lines = [
            f"Severity: {report.severity}",
            f"Incident type: {report.incident_type}",
            f"Root cause: {report.root_cause}",
            f"Affected services: {', '.join(report.affected_services)}",
            "",
            "Executive Summary",
            report.raw_summary,
            "",
        ]
        if plan and plan.steps:
            lines.append("Remediation Steps")
            for step in plan.steps[:10]:
                cmd = f"\n  Command: {step.command}" if step.command else ""
                lines.append(f"{step.order}. [{step.owner}] {step.action}{cmd}")
            lines.append("")
        if cookbook_md:
            lines += ["Runbook (excerpt)", cookbook_md[:2000]]
        return "\n".join(lines)
