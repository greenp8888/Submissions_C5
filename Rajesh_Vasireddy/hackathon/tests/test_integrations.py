"""Tests for Slack and JIRA integrations."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from integrations.slack_client import SlackClient
from integrations.jira_client import JiraClient


# ── Slack ──────────────────────────────────────────────────────────────────────

class TestSlackClient:
    def setup_method(self):
        self.client = SlackClient(webhook_url="https://hooks.slack.com/test")

    def test_build_block_kit_msg_critical(self):
        msg = self.client.build_block_kit_msg(
            severity="CRITICAL",
            incident_type="OOMKill",
            root_cause="Memory exhausted",
            affected_services=["api-server"],
        )
        assert "attachments" in msg
        assert msg["attachments"][0]["color"] == "#FF0000"

    def test_send_success(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            result = self.client.send({"text": "hello"})
        assert result is True

    def test_send_failure(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=500, text="Server Error")
            result = self.client.send({"text": "hello"})
        assert result is False

    def test_send_connection_error(self):
        with patch("requests.post", side_effect=ConnectionError("no network")):
            result = self.client.send({"text": "hello"})
        assert result is False


# ── JIRA ──────────────────────────────────────────────────────────────────────

class TestJiraClient:
    def setup_method(self):
        self.client = JiraClient(
            url="https://example.atlassian.net",
            user="user@example.com",
            token="api-token",
        )

    def test_create_issue_success(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=201,
                json=lambda: {"key": "OPS-42"},
            )
            key = self.client.create_issue(
                project="OPS",
                summary="[CRITICAL] OOMKill",
                description="Full description here",
            )
        assert key == "OPS-42"

    def test_create_issue_auth_failure(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=401, text="Unauthorized"
            )
            key = self.client.create_issue(
                project="OPS", summary="test", description="desc"
            )
        assert key is None

    def test_create_issue_network_error(self):
        with patch("requests.post", side_effect=ConnectionError):
            key = self.client.create_issue(
                project="OPS", summary="test", description="desc"
            )
        assert key is None
