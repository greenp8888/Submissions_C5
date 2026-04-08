"""JIRA integration – REST API v3 client."""

from __future__ import annotations

import logging
from typing import List, Optional

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


class JiraClient:
    """
    Thin wrapper around the JIRA REST API v3.

    Handles authentication (HTTP Basic with an Atlassian API token) and
    converts plain-text descriptions to Atlassian Document Format (ADF)
    before submitting them to the API.
    """

    def __init__(self, url: str, user: str, token: str) -> None:
        """
        Parameters
        ----------
        url:
            Base URL of the JIRA instance, e.g. ``https://yourorg.atlassian.net``.
        user:
            Atlassian account email address (``JIRA_USER`` env var).
        token:
            Atlassian API token (``JIRA_API_TOKEN`` env var).
        """
        self.base_url = url.rstrip("/")
        self.auth = HTTPBasicAuth(user, token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def create_issue(
        self,
        project: str,
        summary: str,
        description: str,
        priority: str = "High",
        labels: Optional[List[str]] = None,
        issue_type: str = "Bug",
    ) -> Optional[str]:
        """
        Creates a JIRA issue and returns the ticket key (e.g. 'OPS-42').
        Returns None if creation fails.
        """
        payload = {
            "fields": {
                "project": {"key": project},
                "summary": summary,
                "description": self._text_to_adf(description),
                "issuetype": {"name": issue_type},
                "priority": {"name": priority},
                "labels": labels or [],
            }
        }

        try:
            resp = requests.post(
                f"{self.base_url}/rest/api/3/issue",
                json=payload,
                auth=self.auth,
                headers=self.headers,
                timeout=15,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                return data.get("key")
            logger.error("JIRA create_issue failed: %s %s", resp.status_code, resp.text)
            return None
        except Exception as exc:
            logger.error("JIRA client error: %s", exc)
            return None

    @staticmethod
    def _text_to_adf(text: str) -> dict:
        """Convert a plain-text description into an Atlassian Document Format doc."""
        content = []
        for block in text.split("\n\n"):
            block = block.strip()
            if block:
                content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": block}],
                })
        return {
            "type": "doc",
            "version": 1,
            "content": content or [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
        }
