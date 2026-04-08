"""Slack integration – Block Kit message builder and webhook sender."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)

SEVERITY_EMOJI = {
    "CRITICAL": ":rotating_light:",
    "HIGH": ":warning:",
    "MEDIUM": ":large_yellow_circle:",
    "LOW": ":large_blue_circle:",
}

SEVERITY_COLOR = {
    "CRITICAL": "#FF0000",
    "HIGH": "#FF8C00",
    "MEDIUM": "#FFD700",
    "LOW": "#36A64F",
}


class SlackClient:
    """
    Builds and sends Slack Block Kit messages via an incoming webhook.

    Severity-to-colour mapping:
    - CRITICAL → red (#FF0000)
    - HIGH     → orange (#FF8C00)
    - MEDIUM   → yellow (#FFD700)
    - LOW      → green (#36A64F)
    """

    def __init__(self, webhook_url: str) -> None:
        """
        Parameters
        ----------
        webhook_url:
            Slack incoming webhook URL (``SLACK_WEBHOOK_URL`` env var).
        """
        self.webhook_url = webhook_url

    # ------------------------------------------------------------------
    # Message builder
    # ------------------------------------------------------------------

    def build_block_kit_msg(
        self,
        severity: str,
        incident_type: str,
        root_cause: str,
        affected_services: List[str],
        runbook_snippet: str = "",
    ) -> Dict[str, Any]:
        """
        Build a Slack Block Kit attachment payload for an incident alert.

        Parameters
        ----------
        severity:
            One of ``CRITICAL``, ``HIGH``, ``MEDIUM``, ``LOW``.
        incident_type:
            Short label for the incident category (e.g. ``"OOMKill"``).
        root_cause:
            One-sentence root cause description.
        affected_services:
            List of service/component names impacted by the incident.
        runbook_snippet:
            Optional runbook excerpt; first 300 characters are shown in the message.

        Returns
        -------
        dict
            A dict with an ``attachments`` key ready to POST to Slack.
        """
        emoji = SEVERITY_EMOJI.get(severity, ":bell:")
        color = SEVERITY_COLOR.get(severity, "#888888")
        services_txt = ", ".join(affected_services) if affected_services else "unknown"

        blocks: List[Dict[str, Any]] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {severity} INCIDENT DETECTED",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Type*\n{incident_type}"},
                    {"type": "mrkdwn", "text": f"*Severity*\n{severity}"},
                    {"type": "mrkdwn", "text": f"*Affected Services*\n{services_txt}"},
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Root Cause*\n{root_cause}"},
            },
        ]

        if runbook_snippet:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Runbook excerpt*\n```{runbook_snippet[:300]}```",
                    },
                }
            )

        return {
            "attachments": [
                {
                    "color": color,
                    "blocks": blocks,
                }
            ]
        }

    # ------------------------------------------------------------------
    # Sender
    # ------------------------------------------------------------------

    def send(self, payload: Dict[str, Any]) -> bool:
        """
        POST *payload* to the Slack incoming webhook.

        Parameters
        ----------
        payload:
            A Block Kit payload dict as returned by :meth:`build_block_kit_msg`.

        Returns
        -------
        bool
            ``True`` on HTTP 200, ``False`` on any error.
        """
        try:
            resp = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            if resp.status_code == 200:
                return True
            logger.error("Slack webhook returned %s: %s", resp.status_code, resp.text)
            return False
        except Exception as exc:
            logger.error("Slack send error: %s", exc)
            return False
