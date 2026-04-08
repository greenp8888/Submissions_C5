"""Log Classifier Agent – parses raw log text and returns a LogReport."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from .base_agent import BaseAgent, extract_json_payload

logger = logging.getLogger(__name__)


@dataclass
class LogReport:
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW  (highest across all detected incidents)
    incident_type: str
    affected_services: List[str]
    root_cause: str
    key_timestamps: List[str]
    error_patterns: List[str]
    raw_summary: str
    confidence: float = 1.0
    sub_incidents: List[dict] = field(default_factory=list)
    """
    All distinct incidents detected in the log, ordered by severity (highest first).
    Each entry: {"severity": str, "incident_type": str, "description": str, "affected_component": str}
    """
    extra: dict = field(default_factory=dict)


SYSTEM_PROMPT = """\
You are a senior Site-Reliability Engineer with deep expertise in Kubernetes,
distributed systems, and cloud-native infrastructure.

Analyze the provided log data and classify the incident. Return ONLY valid JSON.

REQUIRED OUTPUT FORMAT:
{
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "incident_type": "brief label (e.g., OOMKill, DBTimeout, 5xxErrors)",
  "affected_services": ["service1", "service2"],
  "root_cause": "One clear sentence explaining the root cause",
  "key_timestamps": ["ISO8601 timestamp1", "ISO8601 timestamp2"],
  "error_patterns": ["exact error phrase1", "exact error phrase2"],
  "raw_summary": "One paragraph executive summary of the incident",
  "confidence": 0.0-1.0,
  "sub_incidents": [
    {
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "incident_type": "specific incident type",
      "description": "brief description of this specific issue",
      "affected_component": "specific component or service"
    }
  ]
}

SEVERITY GUIDELINES:
- CRITICAL: System down, data loss, security breach, complete service outage
- HIGH: Major functionality broken, significant user impact, urgent fix needed
- MEDIUM: Degraded performance, intermittent issues, non-critical features broken
- LOW: Minor issues, warnings, potential future problems, monitoring alerts

INCIDENT TYPE EXAMPLES:
- OOMKill: Out of memory kills
- DBTimeout: Database connection/query timeouts
- 5xxErrors: HTTP 5xx status codes
- CircuitBreaker: Service circuit breaker activation
- DiskFull: Disk space exhaustion
- NetworkPartition: Network connectivity issues

INSTRUCTIONS:
1. Identify the PRIMARY incident (highest severity)
2. Set top-level fields for the primary incident
3. List ALL distinct incidents in sub_incidents array (including primary)
4. Order sub_incidents by severity (highest first)
5. Extract exact timestamps, error messages, and affected components
6. Be specific and actionable in root_cause and summary

No markdown fences, no extra text, only valid JSON.
"""


class LogClassifierAgent(BaseAgent):
    system_prompt = SYSTEM_PROMPT
    max_tokens = 2048
    model = "anthropic/claude-sonnet-4-5"  # Explicit model for better structured output

    def run(self, raw_log: str) -> LogReport:  # type: ignore[override]
        """Classify *raw_log* and return a :class:`LogReport`."""
        prompt = f"Analyze the following log excerpt:\n\n```\n{raw_log[:12_000]}\n```"
        raw = self._call(prompt)

        try:
            raw = extract_json_payload(raw)
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse JSON from classifier: %s\nRaw: %s", exc, raw[:500])
            raise ValueError("LogClassifierAgent returned non-JSON output.") from exc

        # Validate required fields
        required_fields = ["severity", "incident_type", "affected_services", "root_cause", "raw_summary"]
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            logger.warning("Missing required fields in classifier response: %s", missing_fields)
            # Fill in defaults for missing fields
            for field in missing_fields:
                if field == "severity":
                    data[field] = "UNKNOWN"
                elif field == "incident_type":
                    data[field] = "Unknown"
                elif field == "affected_services":
                    data[field] = []
                elif field == "root_cause":
                    data[field] = "Unable to determine root cause"
                elif field == "raw_summary":
                    data[field] = "Log analysis incomplete"

        return LogReport(
            severity=data.get("severity", "UNKNOWN"),
            incident_type=data.get("incident_type", "Unknown"),
            affected_services=data.get("affected_services", []),
            root_cause=data.get("root_cause", ""),
            key_timestamps=data.get("key_timestamps", []),
            error_patterns=data.get("error_patterns", []),
            raw_summary=data.get("raw_summary", ""),
            confidence=float(data.get("confidence", 1.0)),
            sub_incidents=data.get("sub_incidents", []),
        )
