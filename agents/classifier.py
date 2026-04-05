import json
import time
from langchain_core.messages import SystemMessage, HumanMessage
from orchestrator.state import IncidentState
from utils.llm import get_llm

CLASSIFIER_SYSTEM_PROMPT = """You are a DevOps log analysis expert. Parse the provided ops logs and classify each log entry.

For each log entry, extract:
- timestamp: ISO 8601 format (best effort)
- severity: one of CRITICAL, HIGH, MEDIUM, LOW
- category: e.g. OOM, timeout, auth_failure, disk, network, crash, config_error
- source: the system/service that produced the log
- raw_line: the original log line
- summary: one-sentence description of the issue

Severity guidelines:
- CRITICAL: system down, data loss, OOM kills, crash loops
- HIGH: degraded service, connection pool exhaustion, repeated failures
- MEDIUM: auth failures, intermittent errors, elevated latency
- LOW: warnings, deprecation notices, minor config issues

Return a JSON array of objects. No markdown, no explanation, just the JSON array.

Example input:
2024-01-10 12:00:00 ERROR disk: /dev/sda1 is 95% full

Example output:
[{"timestamp": "2024-01-10T12:00:00Z", "severity": "HIGH", "category": "disk", "source": "disk", "raw_line": "disk: /dev/sda1 is 95% full", "summary": "Root disk nearly full at 95% capacity"}]"""


def classify_logs(state: IncidentState) -> dict:
    start_time = time.time()

    llm = get_llm()
    messages = [
        SystemMessage(content=CLASSIFIER_SYSTEM_PROMPT),
        HumanMessage(content=f"Classify these logs:\n\n{state['raw_logs']}"),
    ]
    response = llm.invoke(messages)

    raw_content = response.content.strip()
    if raw_content.startswith("```"):
        raw_content = raw_content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    classified = json.loads(raw_content)
    end_time = time.time()

    trace_entry = {
        "agent_name": "classifier",
        "start_time": start_time,
        "end_time": end_time,
        "input_summary": f"Raw logs: {len(state['raw_logs'].splitlines())} lines",
        "output_summary": f"Classified {len(classified)} entries",
        "status": "completed",
    }

    return {
        "classified_entries": classified,
        "agent_trace": [trace_entry],
    }
