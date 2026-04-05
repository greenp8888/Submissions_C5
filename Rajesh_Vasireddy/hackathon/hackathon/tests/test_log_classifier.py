"""Tests for LogClassifierAgent."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from agents.log_classifier import LogClassifierAgent, LogReport


OOM_RESPONSE = json.dumps(
    {
        "severity": "CRITICAL",
        "incident_type": "OOMKill",
        "affected_services": ["api-server"],
        "root_cause": "Container exceeded its memory limit and was killed by the OOM killer.",
        "key_timestamps": ["2024-03-15T02:14:22Z", "2024-03-15T02:14:23Z"],
        "error_patterns": ["OOMKilled", "Out of memory: Kill process", "memory limit"],
        "raw_summary": "The api-server pod was OOM killed after exceeding its 4Gi memory limit.",
        "confidence": 0.97,
        "sub_incidents": [
            {
                "severity": "CRITICAL",
                "incident_type": "OOMKill",
                "description": "Container exceeded memory limit and was killed by OOM killer",
                "affected_component": "api-server"
            }
        ]
    }
)


GATEWAY_502_RESPONSE = json.dumps(
    {
        "severity": "HIGH",
        "incident_type": "Gateway502",
        "affected_services": ["nginx", "gateway", "api-backend"],
        "root_cause": "Backend services are failing health checks and circuit breaker has opened.",
        "key_timestamps": ["2024-03-15T10:00:02Z", "2024-03-15T10:00:15Z", "2024-03-15T10:00:16Z"],
        "error_patterns": ["502", "Connection refused", "upstream timed out", "Circuit breaker OPEN", "no live upstreams"],
        "raw_summary": "Gateway is returning 502 errors due to backend service failures. Circuit breaker opened after consecutive failures, and health checks are failing for the API backend pool.",
        "confidence": 0.95,
        "sub_incidents": [
            {
                "severity": "HIGH",
                "incident_type": "CircuitBreaker",
                "description": "Circuit breaker opened for order-service after 10 consecutive failures",
                "affected_component": "gateway"
            },
            {
                "severity": "HIGH",
                "incident_type": "BackendFailure",
                "description": "API backend health checks failing - 0/3 backends healthy",
                "affected_component": "api-backend"
            },
            {
                "severity": "MEDIUM",
                "incident_type": "UpstreamTimeout",
                "description": "Multiple upstream connection timeouts and refused connections",
                "affected_component": "nginx"
            }
        ]
    }
)


@pytest.fixture()
def classifier():
    with patch("agents.base_agent.openai.OpenAI"):
        agent = LogClassifierAgent()
        agent.client = MagicMock()
        return agent


def _mock_response(text: str):
    """Return a mock that matches the OpenAI SDK response shape."""
    response = MagicMock()
    response.choices[0].message.content = text
    return response


def test_classify_oom(classifier):
    classifier.client.chat.completions.create.return_value = _mock_response(OOM_RESPONSE)
    report = classifier.run("Some OOM log content")
    assert isinstance(report, LogReport)
    assert report.severity == "CRITICAL"
    assert report.incident_type == "OOMKill"
    assert "api-server" in report.affected_services
    assert report.confidence == pytest.approx(0.97)
    assert len(report.sub_incidents) == 1
    assert report.sub_incidents[0]["severity"] == "CRITICAL"
    assert report.sub_incidents[0]["incident_type"] == "OOMKill"


def test_classify_gateway_502(classifier):
    classifier.client.chat.completions.create.return_value = _mock_response(GATEWAY_502_RESPONSE)
    report = classifier.run("Some 502 gateway log content")
    assert isinstance(report, LogReport)
    assert report.severity == "HIGH"
    assert report.incident_type == "Gateway502"
    assert "nginx" in report.affected_services
    assert "gateway" in report.affected_services
    assert report.confidence == pytest.approx(0.95)
    assert len(report.sub_incidents) == 3
    # Check that sub_incidents are ordered by severity
    assert report.sub_incidents[0]["severity"] == "HIGH"
    assert report.sub_incidents[1]["severity"] == "HIGH"
    assert report.sub_incidents[2]["severity"] == "MEDIUM"


def test_classify_handles_markdown_fences(classifier):
    fenced = f"```json\n{OOM_RESPONSE}\n```"
    classifier.client.chat.completions.create.return_value = _mock_response(fenced)
    report = classifier.run("log")
    assert report.severity == "CRITICAL"


def test_classify_raises_on_bad_json(classifier):
    classifier.client.chat.completions.create.return_value = _mock_response("not json at all")
    with pytest.raises(ValueError, match="non-JSON"):
        classifier.run("log")
