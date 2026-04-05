"""Tests for RemediationAgent."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from agents.log_classifier import LogReport
from agents.remediation import RemediationAgent, RemediationPlan, RemediationStep

PLAN_RESPONSE = json.dumps(
    {
        "steps": [
            {
                "order": 1,
                "action": "Increase memory limits",
                "command": "kubectl set resources deployment/api-server --limits=memory=8Gi",
                "rationale": "Prevent future OOM kills",
                "owner": "SRE",
                "estimated_minutes": 5,
            }
        ],
        "rollback_plan": "Revert the resource change with kubectl rollout undo.",
        "prevention_notes": "Implement HPA and vertical pod autoscaler.",
    }
)


@pytest.fixture()
def sample_report():
    return LogReport(
        severity="CRITICAL",
        incident_type="OOMKill",
        affected_services=["api-server"],
        root_cause="Container exceeded memory limit.",
        key_timestamps=[],
        error_patterns=["OOMKilled"],
        raw_summary="OOM kill on api-server.",
    )


@pytest.fixture()
def agent():
    with patch("agents.base_agent.openai.OpenAI"):
        a = RemediationAgent()
        a.client = MagicMock()
        return a


def _mock_response(text: str):
    """Return a mock that matches the OpenAI SDK response shape."""
    response = MagicMock()
    response.choices[0].message.content = text
    return response


def test_remediation_returns_plan(agent, sample_report):
    agent.client.chat.completions.create.return_value = _mock_response(PLAN_RESPONSE)
    plan = agent.run(sample_report)
    assert isinstance(plan, RemediationPlan)
    assert len(plan.steps) == 1
    assert plan.steps[0].order == 1
    assert "kubectl" in plan.steps[0].command


def test_remediation_raises_on_bad_json(agent, sample_report):
    agent.client.chat.completions.create.return_value = _mock_response("bad json")
    with pytest.raises(ValueError):
        agent.run(sample_report)


def test_remediation_handles_markdown_fences(agent, sample_report):
    fenced = f"```json\n{PLAN_RESPONSE}\n```"
    agent.client.chat.completions.create.return_value = _mock_response(fenced)
    plan = agent.run(sample_report)
    assert isinstance(plan, RemediationPlan)
    assert len(plan.steps) == 1
    assert plan.steps[0].order == 1
