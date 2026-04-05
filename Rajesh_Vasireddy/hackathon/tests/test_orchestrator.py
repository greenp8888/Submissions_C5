"""Tests for the orchestrator pipeline runner."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from orchestrator.state import IncidentState


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")


def _make_log_report_dict():
    return {
        "severity": "HIGH",
        "incident_type": "Gateway 502",
        "affected_services": ["api-gateway"],
        "root_cause": "Upstream backends unhealthy.",
        "key_timestamps": [],
        "error_patterns": ["502 Bad Gateway"],
        "raw_summary": "High rate of 502s from gateway.",
        "confidence": 0.9,
        "extra": {},
    }


def _make_plan_dict():
    return {
        "incident_type": "Gateway 502",
        "severity": "HIGH",
        "steps": [
            {
                "order": 1,
                "action": "Restart unhealthy pods",
                "command": "kubectl rollout restart deployment/api-gateway",
                "rationale": "Force pod replacement",
                "owner": "SRE",
                "estimated_minutes": 3,
            }
        ],
        "rollback_plan": "Scale down and up.",
        "prevention_notes": "Add readiness probes.",
    }


def test_pipeline_happy_path():
    """Smoke-test: runner returns a finished IncidentState with no errors."""
    with (
        patch("agents.log_classifier.LogClassifierAgent._call") as mock_classify,
        patch("agents.remediation.RemediationAgent._call") as mock_remediate,
        patch("agents.cookbook.CookbookAgent._call") as mock_cookbook,
        patch("agents.notification.NotificationAgent.run", return_value=False),
        patch("agents.jira_agent.JiraAgent.run", return_value=None),
    ):
        import json

        mock_classify.return_value = json.dumps(_make_log_report_dict())
        mock_remediate.return_value = json.dumps(_make_plan_dict())
        mock_cookbook.return_value = "# Runbook\n\n1. Restart pods"

        from orchestrator.runner import run_incident_pipeline

        state = run_incident_pipeline("some log content", filename="test.log")

    assert state["finished"] is True
    assert state["errors"] == []
    assert state["log_report"]["severity"] == "HIGH"
    assert "Runbook" in state["cookbook_md"]
