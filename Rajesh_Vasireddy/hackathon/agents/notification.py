"""Notification Agent – pushes Slack alert for MEDIUM, HIGH, or CRITICAL incidents."""

from __future__ import annotations

import logging
import os

from .base_agent import BaseAgent
from .log_classifier import LogReport

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
NOTIFY_THRESHOLD = "MEDIUM"


class NotificationAgent(BaseAgent):
    """
    Sends Slack Block Kit alerts for incidents at or above MEDIUM severity.

    Threshold: ``NOTIFY_THRESHOLD = "MEDIUM"`` — MEDIUM, HIGH, and CRITICAL
    incidents trigger a Slack message.  Only LOW is silently skipped.

    Requires the ``SLACK_WEBHOOK_URL`` environment variable; if not set the
    step is skipped and recorded in the agent trace without raising an error.
    """

    def run(self, report: LogReport, cookbook_md: str = "") -> bool:  # type: ignore[override]
        """
        Send a Slack notification if the incident severity meets the threshold.

        Parameters
        ----------
        report:
            Classified incident report from :class:`~agents.log_classifier.LogClassifierAgent`.
        cookbook_md:
            Optional runbook markdown; the first 500 characters are included
            as a snippet in the Slack message.

        Returns
        -------
        bool
            ``True`` if the message was successfully delivered, ``False`` if
            skipped (below threshold or missing webhook) or if delivery failed.
        """
        if SEVERITY_ORDER.get(report.severity, 0) < SEVERITY_ORDER[NOTIFY_THRESHOLD]:
            logger.info("Severity %s below threshold – no Slack notification.", report.severity)
            return False

        webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
        if not webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not set – skipping notification.")
            return False

        from integrations.slack_client import SlackClient  # lazy import

        client = SlackClient(webhook_url=webhook_url)
        message = client.build_block_kit_msg(
            severity=report.severity,
            incident_type=report.incident_type,
            root_cause=report.root_cause,
            affected_services=report.affected_services,
            runbook_snippet=cookbook_md[:500] if cookbook_md else "",
        )
        success = client.send(message)
        if success:
            logger.info("Slack notification sent for %s incident.", report.severity)
        return success
