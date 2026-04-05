# DevOps Incident Analysis Suite — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a multi-agent DevOps incident analysis app that classifies ops logs, generates remediations, and pushes output to Slack/JIRA through a Streamlit dashboard.

**Architecture:** Hub-and-spoke LangGraph orchestrator routes dynamically between 5 agents (Log Classifier, Remediation, Cookbook, Slack, JIRA) based on severity. Shared TypedDict state passes data between agents. Streamlit dashboard displays results across 6 tabs with an agent trace view.

**Tech Stack:** Python 3.11+, LangGraph, LangChain + OpenAI (GPT-4o), Streamlit, slack-sdk, python-dotenv

---

## File Map

```
devops-incident-analyzer/
├── app.py                          # Streamlit entry point — sidebar input, tab routing, orchestrator invocation
├── requirements.txt                # All dependencies pinned
├── .env.example                    # Template for OPENAI_API_KEY, SLACK_BOT_TOKEN, SLACK_CHANNEL
├── .gitignore                      # .env, __pycache__, .streamlit/secrets.toml
├── orchestrator/
│   ├── __init__.py                 # Empty
│   ├── state.py                    # IncidentState TypedDict + all data model TypedDicts
│   ├── graph.py                    # LangGraph StateGraph definition, nodes, conditional edges
│   └── router.py                   # get_highest_severity() + route_after_remediation() logic
├── agents/
│   ├── __init__.py                 # Empty
│   ├── classifier.py               # classify_logs(state) → updates classified_entries
│   ├── remediation.py              # generate_remediations(state) → updates remediations
│   ├── cookbook.py                  # synthesize_cookbook(state) → updates cookbook
│   ├── slack_notifier.py           # send_slack_notifications(state) → updates slack_notifications
│   └── jira_ticket.py              # create_jira_tickets(state) → updates jira_tickets
├── ui/
│   ├── __init__.py                 # Empty
│   ├── components.py               # severity_badge(), log_card(), remediation_card(), trace_bar()
│   ├── tabs.py                     # render_analysis_tab(), render_remediations_tab(), etc.
│   └── theme.css                   # Dark theme CSS injected via st.markdown
├── utils/
│   ├── __init__.py                 # Empty
│   ├── log_parser.py               # read_uploaded_file() — handles .log/.json/.csv/.txt
│   └── slack_client.py             # SlackClient wrapper around slack_sdk
├── sample_logs/
│   ├── mixed_incident.log          # Mixed-format demo log
│   ├── k8s_crash.json              # JSON structured K8s logs
│   └── app_errors.csv              # CSV format application errors
└── tests/
    ├── __init__.py                 # Empty
    ├── test_state.py               # State model validation
    ├── test_router.py              # Routing logic tests
    ├── test_classifier.py          # Classifier agent tests
    ├── test_remediation.py         # Remediation agent tests
    ├── test_cookbook.py             # Cookbook agent tests
    ├── test_jira.py                # JIRA mock agent tests
    ├── test_slack.py               # Slack agent tests
    ├── test_graph.py               # End-to-end graph execution tests
    └── test_log_parser.py          # File parsing tests
```

---

### Task 1: Project Scaffolding & Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `orchestrator/__init__.py`
- Create: `agents/__init__.py`
- Create: `ui/__init__.py`
- Create: `utils/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```txt
langgraph==0.4.1
langchain==0.3.25
langchain-openai==0.3.12
streamlit==1.45.1
slack-sdk==3.34.0
python-dotenv==1.1.0
pytest==8.3.5
```

- [ ] **Step 2: Create .env.example**

```
OPENAI_API_KEY=your-openai-api-key-here
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
SLACK_CHANNEL=#incident-alerts
```

- [ ] **Step 3: Create .gitignore**

```
.env
__pycache__/
*.pyc
.streamlit/secrets.toml
.superpowers/
```

- [ ] **Step 4: Create empty __init__.py files**

Create empty `__init__.py` in: `orchestrator/`, `agents/`, `ui/`, `utils/`, `tests/`

- [ ] **Step 5: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: All packages install successfully.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .env.example .gitignore orchestrator/__init__.py agents/__init__.py ui/__init__.py utils/__init__.py tests/__init__.py
git commit -m "feat: scaffold project structure and dependencies"
```

---

### Task 2: Shared State & Data Models

**Files:**
- Create: `orchestrator/state.py`
- Create: `tests/test_state.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_state.py`:

```python
from orchestrator.state import (
    LogEntry,
    Remediation,
    JIRATicket,
    SlackMessage,
    TraceEntry,
    IncidentState,
    make_initial_state,
)


def test_log_entry_has_required_fields():
    entry: LogEntry = {
        "timestamp": "2024-01-15T03:42:18Z",
        "severity": "CRITICAL",
        "category": "OOM",
        "source": "kernel",
        "raw_line": "kernel: Out of memory: Killed process 1842",
        "summary": "OOM kill on api-server container",
    }
    assert entry["severity"] == "CRITICAL"
    assert entry["category"] == "OOM"


def test_remediation_has_required_fields():
    rem: Remediation = {
        "issue_summary": "OOM Kill on api-server",
        "root_cause": "Memory limit too low for workload",
        "fix_steps": ["Increase memory limit to 4Gi", "Add memory monitoring"],
        "rationale": "Container exceeded 2Gi limit during peak traffic",
        "confidence": 0.85,
        "linked_log_entries": [0, 1],
    }
    assert rem["confidence"] == 0.85
    assert len(rem["fix_steps"]) == 2


def test_jira_ticket_has_required_fields():
    ticket: JIRATicket = {
        "title": "CRITICAL: OOM Kill on api-server",
        "description": "Container exceeded memory limit",
        "priority": "Critical",
        "assignee": "oncall-team",
        "labels": ["incident", "OOM"],
    }
    assert ticket["priority"] == "Critical"


def test_slack_message_has_required_fields():
    msg: SlackMessage = {
        "channel": "#incident-alerts",
        "text": "OOM Kill detected",
        "blocks": {"type": "section", "text": {"type": "mrkdwn", "text": "test"}},
        "status": "sent",
    }
    assert msg["status"] == "sent"


def test_trace_entry_has_required_fields():
    trace: TraceEntry = {
        "agent_name": "classifier",
        "start_time": 1000.0,
        "end_time": 1002.1,
        "input_summary": "Raw logs: 27 lines",
        "output_summary": "Classified 27 entries",
        "status": "completed",
    }
    assert trace["status"] == "completed"
    assert trace["end_time"] - trace["start_time"] == pytest.approx(2.1)


def test_make_initial_state():
    state = make_initial_state("some raw logs here")
    assert state["raw_logs"] == "some raw logs here"
    assert state["classified_entries"] == []
    assert state["remediations"] == []
    assert state["cookbook"] == ""
    assert state["jira_tickets"] == []
    assert state["slack_notifications"] == []
    assert state["agent_trace"] == []


import pytest
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_state.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'orchestrator.state'`

- [ ] **Step 3: Write the implementation**

Create `orchestrator/state.py`:

```python
from typing import TypedDict


class LogEntry(TypedDict):
    timestamp: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # OOM, timeout, auth_failure, disk, network, etc.
    source: str
    raw_line: str
    summary: str


class Remediation(TypedDict):
    issue_summary: str
    root_cause: str
    fix_steps: list[str]
    rationale: str
    confidence: float
    linked_log_entries: list[int]


class JIRATicket(TypedDict):
    title: str
    description: str
    priority: str
    assignee: str
    labels: list[str]


class SlackMessage(TypedDict):
    channel: str
    text: str
    blocks: dict
    status: str  # sent, failed


class TraceEntry(TypedDict):
    agent_name: str
    start_time: float
    end_time: float
    input_summary: str
    output_summary: str
    status: str  # running, completed, skipped, failed


class IncidentState(TypedDict):
    raw_logs: str
    classified_entries: list[LogEntry]
    remediations: list[Remediation]
    cookbook: str
    jira_tickets: list[JIRATicket]
    slack_notifications: list[SlackMessage]
    agent_trace: list[TraceEntry]


def make_initial_state(raw_logs: str) -> IncidentState:
    return {
        "raw_logs": raw_logs,
        "classified_entries": [],
        "remediations": [],
        "cookbook": "",
        "jira_tickets": [],
        "slack_notifications": [],
        "agent_trace": [],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_state.py -v`
Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add orchestrator/state.py tests/test_state.py
git commit -m "feat: add shared state TypedDicts and data models"
```

---

### Task 3: Routing Logic

**Files:**
- Create: `orchestrator/router.py`
- Create: `tests/test_router.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_router.py`:

```python
from orchestrator.router import get_highest_severity, route_after_remediation
from orchestrator.state import make_initial_state


def test_highest_severity_critical():
    state = make_initial_state("")
    state["classified_entries"] = [
        {"timestamp": "", "severity": "LOW", "category": "", "source": "", "raw_line": "", "summary": ""},
        {"timestamp": "", "severity": "CRITICAL", "category": "", "source": "", "raw_line": "", "summary": ""},
        {"timestamp": "", "severity": "MEDIUM", "category": "", "source": "", "raw_line": "", "summary": ""},
    ]
    assert get_highest_severity(state) == "CRITICAL"


def test_highest_severity_medium_only():
    state = make_initial_state("")
    state["classified_entries"] = [
        {"timestamp": "", "severity": "MEDIUM", "category": "", "source": "", "raw_line": "", "summary": ""},
        {"timestamp": "", "severity": "LOW", "category": "", "source": "", "raw_line": "", "summary": ""},
    ]
    assert get_highest_severity(state) == "MEDIUM"


def test_highest_severity_all_low():
    state = make_initial_state("")
    state["classified_entries"] = [
        {"timestamp": "", "severity": "LOW", "category": "", "source": "", "raw_line": "", "summary": ""},
    ]
    assert get_highest_severity(state) == "LOW"


def test_highest_severity_high():
    state = make_initial_state("")
    state["classified_entries"] = [
        {"timestamp": "", "severity": "HIGH", "category": "", "source": "", "raw_line": "", "summary": ""},
        {"timestamp": "", "severity": "MEDIUM", "category": "", "source": "", "raw_line": "", "summary": ""},
    ]
    assert get_highest_severity(state) == "HIGH"


def test_route_critical_returns_all_agents():
    state = make_initial_state("")
    state["classified_entries"] = [
        {"timestamp": "", "severity": "CRITICAL", "category": "", "source": "", "raw_line": "", "summary": ""},
    ]
    state["remediations"] = [
        {"issue_summary": "x", "root_cause": "y", "fix_steps": [], "rationale": "", "confidence": 0.9, "linked_log_entries": [0]},
    ]
    result = route_after_remediation(state)
    assert set(result) == {"slack_notifier", "jira_ticket", "cookbook"}


def test_route_medium_returns_slack_and_cookbook():
    state = make_initial_state("")
    state["classified_entries"] = [
        {"timestamp": "", "severity": "MEDIUM", "category": "", "source": "", "raw_line": "", "summary": ""},
    ]
    state["remediations"] = [
        {"issue_summary": "x", "root_cause": "y", "fix_steps": [], "rationale": "", "confidence": 0.9, "linked_log_entries": [0]},
    ]
    result = route_after_remediation(state)
    assert set(result) == {"slack_notifier", "cookbook"}


def test_route_low_returns_cookbook_only():
    state = make_initial_state("")
    state["classified_entries"] = [
        {"timestamp": "", "severity": "LOW", "category": "", "source": "", "raw_line": "", "summary": ""},
    ]
    state["remediations"] = [
        {"issue_summary": "x", "root_cause": "y", "fix_steps": [], "rationale": "", "confidence": 0.9, "linked_log_entries": [0]},
    ]
    result = route_after_remediation(state)
    assert result == ["cookbook"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_router.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'orchestrator.router'`

- [ ] **Step 3: Write the implementation**

Create `orchestrator/router.py`:

```python
from orchestrator.state import IncidentState

SEVERITY_ORDER = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


def get_highest_severity(state: IncidentState) -> str:
    entries = state["classified_entries"]
    if not entries:
        return "LOW"
    return max(entries, key=lambda e: SEVERITY_ORDER.get(e["severity"], 0))["severity"]


def route_after_remediation(state: IncidentState) -> list[str]:
    highest = get_highest_severity(state)
    severity_rank = SEVERITY_ORDER.get(highest, 0)

    if severity_rank >= 3:  # CRITICAL or HIGH
        return ["slack_notifier", "jira_ticket", "cookbook"]
    elif severity_rank == 2:  # MEDIUM
        return ["slack_notifier", "cookbook"]
    else:  # LOW
        return ["cookbook"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_router.py -v`
Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add orchestrator/router.py tests/test_router.py
git commit -m "feat: add severity-based routing logic"
```

---

### Task 4: Log Classifier Agent

**Files:**
- Create: `agents/classifier.py`
- Create: `tests/test_classifier.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_classifier.py`:

```python
import json
from unittest.mock import patch, MagicMock
from orchestrator.state import make_initial_state
from agents.classifier import classify_logs

SAMPLE_LOGS = """2024-01-15 03:42:18 ERROR kernel: Out of memory: Killed process 1842 (node) total-vm:2451832kB
2024-01-15 03:42:20 WARN sqlalchemy.exc.TimeoutError: QueuePool limit of 20 overflow 10 reached
2024-01-15 03:43:01 ERROR auth.middleware: JWT validation failed: token expired"""

MOCK_LLM_RESPONSE = json.dumps([
    {
        "timestamp": "2024-01-15T03:42:18Z",
        "severity": "CRITICAL",
        "category": "OOM",
        "source": "kernel",
        "raw_line": "kernel: Out of memory: Killed process 1842 (node) total-vm:2451832kB",
        "summary": "OOM kill on node process, VM size 2.4GB",
    },
    {
        "timestamp": "2024-01-15T03:42:20Z",
        "severity": "HIGH",
        "category": "timeout",
        "source": "sqlalchemy",
        "raw_line": "sqlalchemy.exc.TimeoutError: QueuePool limit of 20 overflow 10 reached",
        "summary": "Database connection pool exhausted",
    },
    {
        "timestamp": "2024-01-15T03:43:01Z",
        "severity": "MEDIUM",
        "category": "auth_failure",
        "source": "auth.middleware",
        "raw_line": "auth.middleware: JWT validation failed: token expired",
        "summary": "JWT token expired causing auth failure",
    },
])


@patch("agents.classifier.ChatOpenAI")
def test_classify_logs_parses_response(mock_chat_class):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content=MOCK_LLM_RESPONSE)
    mock_chat_class.return_value = mock_llm

    state = make_initial_state(SAMPLE_LOGS)
    result = classify_logs(state)

    assert len(result["classified_entries"]) == 3
    assert result["classified_entries"][0]["severity"] == "CRITICAL"
    assert result["classified_entries"][1]["category"] == "timeout"
    assert result["classified_entries"][2]["source"] == "auth.middleware"


@patch("agents.classifier.ChatOpenAI")
def test_classify_logs_adds_trace_entry(mock_chat_class):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content=MOCK_LLM_RESPONSE)
    mock_chat_class.return_value = mock_llm

    state = make_initial_state(SAMPLE_LOGS)
    result = classify_logs(state)

    assert len(result["agent_trace"]) == 1
    trace = result["agent_trace"][0]
    assert trace["agent_name"] == "classifier"
    assert trace["status"] == "completed"
    assert trace["end_time"] >= trace["start_time"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_classifier.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.classifier'`

- [ ] **Step 3: Write the implementation**

Create `agents/classifier.py`:

```python
import json
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from orchestrator.state import IncidentState

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

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
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
        "agent_trace": state.get("agent_trace", []) + [trace_entry],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_classifier.py -v`
Expected: All 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add agents/classifier.py tests/test_classifier.py
git commit -m "feat: add log classifier agent with LLM-based parsing"
```

---

### Task 5: Remediation Agent

**Files:**
- Create: `agents/remediation.py`
- Create: `tests/test_remediation.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_remediation.py`:

```python
import json
from unittest.mock import patch, MagicMock
from orchestrator.state import make_initial_state
from agents.remediation import generate_remediations

SAMPLE_CLASSIFIED = [
    {
        "timestamp": "2024-01-15T03:42:18Z",
        "severity": "CRITICAL",
        "category": "OOM",
        "source": "kernel",
        "raw_line": "kernel: Out of memory: Killed process 1842",
        "summary": "OOM kill on node process",
    },
    {
        "timestamp": "2024-01-15T03:42:20Z",
        "severity": "HIGH",
        "category": "timeout",
        "source": "sqlalchemy",
        "raw_line": "sqlalchemy.exc.TimeoutError: QueuePool limit reached",
        "summary": "Database connection pool exhausted",
    },
]

MOCK_LLM_RESPONSE = json.dumps([
    {
        "issue_summary": "OOM Kill on node process",
        "root_cause": "Container memory limit (2Gi) insufficient for workload",
        "fix_steps": ["Increase memory limit to 4Gi in deployment spec", "Add memory usage alerting at 80% threshold"],
        "rationale": "Process was killed by kernel OOM killer, indicating the configured limit is too low for the actual workload",
        "confidence": 0.9,
        "linked_log_entries": [0],
    },
    {
        "issue_summary": "Database connection pool exhaustion",
        "root_cause": "Pool size of 20 with overflow 10 cannot handle concurrent request volume",
        "fix_steps": ["Increase pool_size to 40 and max_overflow to 20", "Add connection pool monitoring"],
        "rationale": "TimeoutError indicates all 30 connections (20 + 10 overflow) were in use simultaneously",
        "confidence": 0.85,
        "linked_log_entries": [1],
    },
])


@patch("agents.remediation.ChatOpenAI")
def test_generate_remediations_parses_response(mock_chat_class):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content=MOCK_LLM_RESPONSE)
    mock_chat_class.return_value = mock_llm

    state = make_initial_state("")
    state["classified_entries"] = SAMPLE_CLASSIFIED
    result = generate_remediations(state)

    assert len(result["remediations"]) == 2
    assert result["remediations"][0]["confidence"] == 0.9
    assert "memory limit" in result["remediations"][0]["fix_steps"][0].lower()


@patch("agents.remediation.ChatOpenAI")
def test_generate_remediations_adds_trace(mock_chat_class):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content=MOCK_LLM_RESPONSE)
    mock_chat_class.return_value = mock_llm

    state = make_initial_state("")
    state["classified_entries"] = SAMPLE_CLASSIFIED
    result = generate_remediations(state)

    trace = [t for t in result["agent_trace"] if t["agent_name"] == "remediation"]
    assert len(trace) == 1
    assert trace[0]["status"] == "completed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_remediation.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.remediation'`

- [ ] **Step 3: Write the implementation**

Create `agents/remediation.py`:

```python
import json
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from orchestrator.state import IncidentState

REMEDIATION_SYSTEM_PROMPT = """You are a senior SRE/DevOps engineer. Given classified log entries, generate remediations.

For each distinct issue (group related log entries), produce:
- issue_summary: one-line description of the issue
- root_cause: what is causing this issue
- fix_steps: ordered list of actionable fix steps (commands, config changes, etc.)
- rationale: why this fix addresses the root cause
- confidence: 0.0-1.0 how confident you are in this diagnosis
- linked_log_entries: list of indices (0-based) into the input entries that relate to this issue

Group related entries into a single remediation. Do not create separate remediations for the same underlying issue.

Return a JSON array. No markdown, no explanation, just the JSON array."""


def generate_remediations(state: IncidentState) -> dict:
    start_time = time.time()

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    entries_json = json.dumps(state["classified_entries"], indent=2)
    messages = [
        SystemMessage(content=REMEDIATION_SYSTEM_PROMPT),
        HumanMessage(content=f"Generate remediations for these classified entries:\n\n{entries_json}"),
    ]
    response = llm.invoke(messages)

    raw_content = response.content.strip()
    if raw_content.startswith("```"):
        raw_content = raw_content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    remediations = json.loads(raw_content)
    end_time = time.time()

    trace_entry = {
        "agent_name": "remediation",
        "start_time": start_time,
        "end_time": end_time,
        "input_summary": f"Classified entries: {len(state['classified_entries'])} issues",
        "output_summary": f"Generated {len(remediations)} remediations",
        "status": "completed",
    }

    return {
        "remediations": remediations,
        "agent_trace": state.get("agent_trace", []) + [trace_entry],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_remediation.py -v`
Expected: All 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add agents/remediation.py tests/test_remediation.py
git commit -m "feat: add remediation agent with root cause analysis"
```

---

### Task 6: Cookbook Synthesizer Agent

**Files:**
- Create: `agents/cookbook.py`
- Create: `tests/test_cookbook.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_cookbook.py`:

```python
from unittest.mock import patch, MagicMock
from orchestrator.state import make_initial_state
from agents.cookbook import synthesize_cookbook

SAMPLE_REMEDIATIONS = [
    {
        "issue_summary": "OOM Kill on api-server",
        "root_cause": "Memory limit too low",
        "fix_steps": ["Increase memory limit to 4Gi"],
        "rationale": "Process exceeded 2Gi limit",
        "confidence": 0.9,
        "linked_log_entries": [0],
    },
    {
        "issue_summary": "DB connection pool exhaustion",
        "root_cause": "Pool size too small",
        "fix_steps": ["Increase pool_size to 40"],
        "rationale": "All connections in use",
        "confidence": 0.85,
        "linked_log_entries": [1],
    },
]

MOCK_COOKBOOK = """# Incident Response Runbook

## Priority 1: Critical Issues

### OOM Kill on api-server
- [ ] Increase memory limit to 4Gi in deployment spec
- [ ] Verify pod restarts cleanly with new limit

## Priority 2: High Issues

### DB connection pool exhaustion
- [ ] Increase pool_size to 40 in database config
- [ ] Monitor connection count after change"""


@patch("agents.cookbook.ChatOpenAI")
def test_synthesize_cookbook_returns_markdown(mock_chat_class):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content=MOCK_COOKBOOK)
    mock_chat_class.return_value = mock_llm

    state = make_initial_state("")
    state["remediations"] = SAMPLE_REMEDIATIONS
    result = synthesize_cookbook(state)

    assert "# Incident Response Runbook" in result["cookbook"]
    assert "OOM Kill" in result["cookbook"]
    assert "- [ ]" in result["cookbook"]


@patch("agents.cookbook.ChatOpenAI")
def test_synthesize_cookbook_adds_trace(mock_chat_class):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content=MOCK_COOKBOOK)
    mock_chat_class.return_value = mock_llm

    state = make_initial_state("")
    state["remediations"] = SAMPLE_REMEDIATIONS
    result = synthesize_cookbook(state)

    trace = [t for t in result["agent_trace"] if t["agent_name"] == "cookbook"]
    assert len(trace) == 1
    assert trace[0]["status"] == "completed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cookbook.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.cookbook'`

- [ ] **Step 3: Write the implementation**

Create `agents/cookbook.py`:

```python
import json
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from orchestrator.state import IncidentState

COOKBOOK_SYSTEM_PROMPT = """You are a senior SRE creating an incident response runbook.

Given a list of remediations, create a markdown checklist that an oncall engineer can follow step-by-step.

Requirements:
- Group by priority (Critical first, then High, Medium, Low)
- Each fix step is a checkbox item (- [ ])
- Include verification steps after each fix
- Deduplicate if multiple remediations address the same system
- Keep it actionable — commands, config paths, specific values

Return only the markdown. No preamble or explanation."""


def synthesize_cookbook(state: IncidentState) -> dict:
    start_time = time.time()

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    remediations_json = json.dumps(state["remediations"], indent=2)
    messages = [
        SystemMessage(content=COOKBOOK_SYSTEM_PROMPT),
        HumanMessage(content=f"Create a runbook from these remediations:\n\n{remediations_json}"),
    ]
    response = llm.invoke(messages)
    end_time = time.time()

    trace_entry = {
        "agent_name": "cookbook",
        "start_time": start_time,
        "end_time": end_time,
        "input_summary": f"Remediations: {len(state['remediations'])} items",
        "output_summary": "Generated incident response runbook",
        "status": "completed",
    }

    return {
        "cookbook": response.content.strip(),
        "agent_trace": state.get("agent_trace", []) + [trace_entry],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cookbook.py -v`
Expected: All 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add agents/cookbook.py tests/test_cookbook.py
git commit -m "feat: add cookbook synthesizer agent"
```

---

### Task 7: Slack Notification Agent

**Files:**
- Create: `utils/slack_client.py`
- Create: `agents/slack_notifier.py`
- Create: `tests/test_slack.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_slack.py`:

```python
import os
from unittest.mock import patch, MagicMock
from orchestrator.state import make_initial_state
from agents.slack_notifier import send_slack_notifications

SAMPLE_REMEDIATIONS = [
    {
        "issue_summary": "OOM Kill on api-server",
        "root_cause": "Memory limit too low",
        "fix_steps": ["Increase memory limit to 4Gi"],
        "rationale": "Process exceeded 2Gi limit",
        "confidence": 0.9,
        "linked_log_entries": [0],
    },
]


@patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-test", "SLACK_CHANNEL": "#test"})
@patch("agents.slack_notifier.WebClient")
def test_send_slack_notifications_posts_message(mock_webclient_class):
    mock_client = MagicMock()
    mock_client.chat_postMessage.return_value = {"ok": True}
    mock_webclient_class.return_value = mock_client

    state = make_initial_state("")
    state["remediations"] = SAMPLE_REMEDIATIONS
    result = send_slack_notifications(state)

    assert len(result["slack_notifications"]) == 1
    assert result["slack_notifications"][0]["status"] == "sent"
    mock_client.chat_postMessage.assert_called_once()


@patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-test", "SLACK_CHANNEL": "#test"})
@patch("agents.slack_notifier.WebClient")
def test_send_slack_handles_failure(mock_webclient_class):
    mock_client = MagicMock()
    mock_client.chat_postMessage.side_effect = Exception("channel_not_found")
    mock_webclient_class.return_value = mock_client

    state = make_initial_state("")
    state["remediations"] = SAMPLE_REMEDIATIONS
    result = send_slack_notifications(state)

    assert len(result["slack_notifications"]) == 1
    assert result["slack_notifications"][0]["status"] == "failed"


@patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-test", "SLACK_CHANNEL": "#test"})
@patch("agents.slack_notifier.WebClient")
def test_send_slack_adds_trace(mock_webclient_class):
    mock_client = MagicMock()
    mock_client.chat_postMessage.return_value = {"ok": True}
    mock_webclient_class.return_value = mock_client

    state = make_initial_state("")
    state["remediations"] = SAMPLE_REMEDIATIONS
    result = send_slack_notifications(state)

    trace = [t for t in result["agent_trace"] if t["agent_name"] == "slack_notifier"]
    assert len(trace) == 1
    assert trace[0]["status"] == "completed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_slack.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.slack_notifier'`

- [ ] **Step 3: Write the Slack client utility**

Create `utils/slack_client.py`:

```python
import os
from slack_sdk import WebClient


def get_slack_client() -> WebClient:
    token = os.environ.get("SLACK_BOT_TOKEN", "")
    return WebClient(token=token)


def get_slack_channel() -> str:
    return os.environ.get("SLACK_CHANNEL", "#incident-alerts")
```

- [ ] **Step 4: Write the agent implementation**

Create `agents/slack_notifier.py`:

```python
import os
import time
from slack_sdk import WebClient
from orchestrator.state import IncidentState

SEVERITY_EMOJI = {
    "CRITICAL": ":red_circle:",
    "HIGH": ":large_orange_circle:",
    "MEDIUM": ":large_blue_circle:",
    "LOW": ":white_circle:",
}


def _build_slack_blocks(remediations: list[dict]) -> list[dict]:
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Incident Analysis Report"},
        },
        {"type": "divider"},
    ]

    for rem in remediations:
        severity = "CRITICAL"
        for entry_idx in rem.get("linked_log_entries", []):
            break
        emoji = SEVERITY_EMOJI.get(severity, ":white_circle:")

        fix_text = "\n".join(f"  {i+1}. {step}" for i, step in enumerate(rem["fix_steps"]))
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"{emoji} *{rem['issue_summary']}*\n"
                    f"*Root cause:* {rem['root_cause']}\n"
                    f"*Fix steps:*\n{fix_text}\n"
                    f"_Confidence: {rem['confidence']:.0%}_"
                ),
            },
        })
        blocks.append({"type": "divider"})

    return blocks


def send_slack_notifications(state: IncidentState) -> dict:
    start_time = time.time()

    token = os.environ.get("SLACK_BOT_TOKEN", "")
    channel = os.environ.get("SLACK_CHANNEL", "#incident-alerts")
    client = WebClient(token=token)

    remediations = state["remediations"]
    blocks = _build_slack_blocks(remediations)
    fallback_text = f"Incident Analysis: {len(remediations)} issues found"

    notifications = []
    try:
        client.chat_postMessage(channel=channel, text=fallback_text, blocks=blocks)
        notifications.append({
            "channel": channel,
            "text": fallback_text,
            "blocks": {"blocks": blocks},
            "status": "sent",
        })
    except Exception:
        notifications.append({
            "channel": channel,
            "text": fallback_text,
            "blocks": {"blocks": blocks},
            "status": "failed",
        })

    end_time = time.time()

    trace_entry = {
        "agent_name": "slack_notifier",
        "start_time": start_time,
        "end_time": end_time,
        "input_summary": f"Remediations: {len(remediations)} items",
        "output_summary": f"Sent {sum(1 for n in notifications if n['status'] == 'sent')} messages",
        "status": "completed",
    }

    return {
        "slack_notifications": notifications,
        "agent_trace": state.get("agent_trace", []) + [trace_entry],
    }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_slack.py -v`
Expected: All 3 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add utils/slack_client.py agents/slack_notifier.py tests/test_slack.py
git commit -m "feat: add Slack notification agent with Block Kit formatting"
```

---

### Task 8: JIRA Ticket Agent (Mocked)

**Files:**
- Create: `agents/jira_ticket.py`
- Create: `tests/test_jira.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_jira.py`:

```python
import json
from unittest.mock import patch, MagicMock
from orchestrator.state import make_initial_state
from agents.jira_ticket import create_jira_tickets

SAMPLE_CLASSIFIED = [
    {"timestamp": "", "severity": "CRITICAL", "category": "OOM", "source": "kernel", "raw_line": "", "summary": "OOM kill"},
    {"timestamp": "", "severity": "HIGH", "category": "timeout", "source": "sqlalchemy", "raw_line": "", "summary": "DB pool exhausted"},
    {"timestamp": "", "severity": "LOW", "category": "config", "source": "app", "raw_line": "", "summary": "Deprecated config key"},
]

SAMPLE_REMEDIATIONS = [
    {
        "issue_summary": "OOM Kill on api-server",
        "root_cause": "Memory limit too low",
        "fix_steps": ["Increase memory limit to 4Gi"],
        "rationale": "Process exceeded 2Gi limit",
        "confidence": 0.9,
        "linked_log_entries": [0],
    },
    {
        "issue_summary": "DB connection pool exhaustion",
        "root_cause": "Pool size too small",
        "fix_steps": ["Increase pool_size to 40"],
        "rationale": "All connections in use",
        "confidence": 0.85,
        "linked_log_entries": [1],
    },
    {
        "issue_summary": "Deprecated config warning",
        "root_cause": "Old config key still in use",
        "fix_steps": ["Update config key name"],
        "rationale": "Non-breaking but should be fixed",
        "confidence": 0.95,
        "linked_log_entries": [2],
    },
]

MOCK_LLM_RESPONSE = json.dumps([
    {
        "title": "CRITICAL: OOM Kill on api-server",
        "description": "Container exceeded memory limit (2Gi). Increase to 4Gi.",
        "priority": "Critical",
        "assignee": "oncall-team",
        "labels": ["incident", "OOM", "critical"],
    },
    {
        "title": "HIGH: DB connection pool exhaustion",
        "description": "Pool size of 20 insufficient. Increase to 40.",
        "priority": "High",
        "assignee": "oncall-team",
        "labels": ["incident", "database", "high"],
    },
])


@patch("agents.jira_ticket.ChatOpenAI")
def test_create_jira_tickets_filters_critical_high(mock_chat_class):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content=MOCK_LLM_RESPONSE)
    mock_chat_class.return_value = mock_llm

    state = make_initial_state("")
    state["classified_entries"] = SAMPLE_CLASSIFIED
    state["remediations"] = SAMPLE_REMEDIATIONS
    result = create_jira_tickets(state)

    assert len(result["jira_tickets"]) == 2
    assert result["jira_tickets"][0]["priority"] == "Critical"


@patch("agents.jira_ticket.ChatOpenAI")
def test_create_jira_tickets_adds_trace(mock_chat_class):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content=MOCK_LLM_RESPONSE)
    mock_chat_class.return_value = mock_llm

    state = make_initial_state("")
    state["classified_entries"] = SAMPLE_CLASSIFIED
    state["remediations"] = SAMPLE_REMEDIATIONS
    result = create_jira_tickets(state)

    trace = [t for t in result["agent_trace"] if t["agent_name"] == "jira_ticket"]
    assert len(trace) == 1
    assert trace[0]["status"] == "completed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_jira.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.jira_ticket'`

- [ ] **Step 3: Write the implementation**

Create `agents/jira_ticket.py`:

```python
import json
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from orchestrator.state import IncidentState

JIRA_SYSTEM_PROMPT = """You are a DevOps engineer creating JIRA tickets for critical incidents.

Given remediations for CRITICAL and HIGH severity issues, create JIRA ticket objects.

For each ticket produce:
- title: "[SEVERITY]: Brief issue description"
- description: Detailed description including root cause, fix steps, and rationale
- priority: "Critical" or "High" (matching the severity)
- assignee: "oncall-team"
- labels: list of relevant tags (e.g., "incident", category, severity)

Return a JSON array. No markdown, no explanation, just the JSON array."""


def create_jira_tickets(state: IncidentState) -> dict:
    start_time = time.time()

    # Filter remediations linked to CRITICAL/HIGH entries
    high_sev_indices = set()
    for i, entry in enumerate(state["classified_entries"]):
        if entry["severity"] in ("CRITICAL", "HIGH"):
            high_sev_indices.add(i)

    critical_remediations = [
        rem for rem in state["remediations"]
        if any(idx in high_sev_indices for idx in rem["linked_log_entries"])
    ]

    if not critical_remediations:
        end_time = time.time()
        return {
            "jira_tickets": [],
            "agent_trace": state.get("agent_trace", []) + [{
                "agent_name": "jira_ticket",
                "start_time": start_time,
                "end_time": end_time,
                "input_summary": "No critical/high remediations",
                "output_summary": "No tickets created",
                "status": "completed",
            }],
        }

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    remediations_json = json.dumps(critical_remediations, indent=2)
    messages = [
        SystemMessage(content=JIRA_SYSTEM_PROMPT),
        HumanMessage(content=f"Create JIRA tickets for these remediations:\n\n{remediations_json}"),
    ]
    response = llm.invoke(messages)

    raw_content = response.content.strip()
    if raw_content.startswith("```"):
        raw_content = raw_content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    tickets = json.loads(raw_content)
    end_time = time.time()

    trace_entry = {
        "agent_name": "jira_ticket",
        "start_time": start_time,
        "end_time": end_time,
        "input_summary": f"Critical/High remediations: {len(critical_remediations)} items",
        "output_summary": f"Created {len(tickets)} JIRA tickets (mocked)",
        "status": "completed",
    }

    return {
        "jira_tickets": tickets,
        "agent_trace": state.get("agent_trace", []) + [trace_entry],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_jira.py -v`
Expected: All 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add agents/jira_ticket.py tests/test_jira.py
git commit -m "feat: add mocked JIRA ticket agent"
```

---

### Task 9: LangGraph Orchestrator

**Files:**
- Create: `orchestrator/graph.py`
- Create: `tests/test_graph.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_graph.py`:

```python
import json
from unittest.mock import patch, MagicMock
from orchestrator.graph import build_graph
from orchestrator.state import make_initial_state

MOCK_CLASSIFIED = [
    {
        "timestamp": "2024-01-15T03:42:18Z",
        "severity": "CRITICAL",
        "category": "OOM",
        "source": "kernel",
        "raw_line": "kernel: OOM killed process",
        "summary": "OOM kill",
    },
]

MOCK_REMEDIATIONS = [
    {
        "issue_summary": "OOM Kill",
        "root_cause": "Memory limit too low",
        "fix_steps": ["Increase memory limit"],
        "rationale": "Process exceeded limit",
        "confidence": 0.9,
        "linked_log_entries": [0],
    },
]

MOCK_COOKBOOK = "# Runbook\n- [ ] Increase memory limit"

MOCK_TICKETS = [
    {
        "title": "CRITICAL: OOM Kill",
        "description": "Increase memory",
        "priority": "Critical",
        "assignee": "oncall-team",
        "labels": ["incident"],
    },
]


@patch("agents.jira_ticket.ChatOpenAI")
@patch("agents.slack_notifier.WebClient")
@patch("agents.cookbook.ChatOpenAI")
@patch("agents.remediation.ChatOpenAI")
@patch("agents.classifier.ChatOpenAI")
def test_graph_runs_all_agents_for_critical(
    mock_classifier_llm,
    mock_remediation_llm,
    mock_cookbook_llm,
    mock_slack_client,
    mock_jira_llm,
):
    # Setup classifier mock
    mock_cls = MagicMock()
    mock_cls.invoke.return_value = MagicMock(content=json.dumps(MOCK_CLASSIFIED))
    mock_classifier_llm.return_value = mock_cls

    # Setup remediation mock
    mock_rem = MagicMock()
    mock_rem.invoke.return_value = MagicMock(content=json.dumps(MOCK_REMEDIATIONS))
    mock_remediation_llm.return_value = mock_rem

    # Setup cookbook mock
    mock_cb = MagicMock()
    mock_cb.invoke.return_value = MagicMock(content=MOCK_COOKBOOK)
    mock_cookbook_llm.return_value = mock_cb

    # Setup slack mock
    mock_sc = MagicMock()
    mock_sc.chat_postMessage.return_value = {"ok": True}
    mock_slack_client.return_value = mock_sc

    # Setup jira mock
    mock_jr = MagicMock()
    mock_jr.invoke.return_value = MagicMock(content=json.dumps(MOCK_TICKETS))
    mock_jira_llm.return_value = mock_jr

    graph = build_graph()
    initial_state = make_initial_state("2024-01-15 03:42:18 ERROR kernel: OOM killed process")

    with patch.dict("os.environ", {"SLACK_BOT_TOKEN": "xoxb-test", "SLACK_CHANNEL": "#test"}):
        result = graph.invoke(initial_state)

    assert len(result["classified_entries"]) == 1
    assert len(result["remediations"]) == 1
    assert "Runbook" in result["cookbook"]
    assert len(result["jira_tickets"]) == 1
    assert len(result["slack_notifications"]) == 1
    assert len(result["agent_trace"]) >= 5


def test_build_graph_returns_compiled_graph():
    graph = build_graph()
    assert graph is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_graph.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'orchestrator.graph'`

- [ ] **Step 3: Write the implementation**

Create `orchestrator/graph.py`:

```python
from langgraph.graph import StateGraph, END
from orchestrator.state import IncidentState
from orchestrator.router import route_after_remediation
from agents.classifier import classify_logs
from agents.remediation import generate_remediations
from agents.cookbook import synthesize_cookbook
from agents.slack_notifier import send_slack_notifications
from agents.jira_ticket import create_jira_tickets


def _merge_trace(existing: list, new_entries: list) -> list:
    """Merge trace entries, avoiding duplicates by agent_name + start_time."""
    seen = {(t["agent_name"], t["start_time"]) for t in existing}
    merged = list(existing)
    for entry in new_entries:
        key = (entry["agent_name"], entry["start_time"])
        if key not in seen:
            merged.append(entry)
            seen.add(key)
    return merged


def _classifier_node(state: IncidentState) -> dict:
    return classify_logs(state)


def _remediation_node(state: IncidentState) -> dict:
    return generate_remediations(state)


def _cookbook_node(state: IncidentState) -> dict:
    return synthesize_cookbook(state)


def _slack_node(state: IncidentState) -> dict:
    return send_slack_notifications(state)


def _jira_node(state: IncidentState) -> dict:
    return create_jira_tickets(state)


def _route_after_remediation(state: IncidentState) -> list[str]:
    return route_after_remediation(state)


def _fanout_complete(state: IncidentState) -> str:
    return END


def build_graph():
    graph = StateGraph(IncidentState)

    # Add nodes
    graph.add_node("classifier", _classifier_node)
    graph.add_node("remediation", _remediation_node)
    graph.add_node("cookbook", _cookbook_node)
    graph.add_node("slack_notifier", _slack_node)
    graph.add_node("jira_ticket", _jira_node)

    # Linear: start → classifier → remediation
    graph.set_entry_point("classifier")
    graph.add_edge("classifier", "remediation")

    # Conditional fan-out after remediation
    graph.add_conditional_edges(
        "remediation",
        _route_after_remediation,
        {
            "cookbook": "cookbook",
            "slack_notifier": "slack_notifier",
            "jira_ticket": "jira_ticket",
        },
    )

    # Fan-out agents all go to END
    graph.add_edge("cookbook", END)
    graph.add_edge("slack_notifier", END)
    graph.add_edge("jira_ticket", END)

    return graph.compile()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_graph.py -v`
Expected: All 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add orchestrator/graph.py tests/test_graph.py
git commit -m "feat: add LangGraph orchestrator with conditional fan-out"
```

---

### Task 10: Log Parser Utility

**Files:**
- Create: `utils/log_parser.py`
- Create: `tests/test_log_parser.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_log_parser.py`:

```python
import io
from utils.log_parser import read_uploaded_file


def test_read_text_file():
    content = b"2024-01-15 ERROR something broke\n2024-01-15 WARN disk full"
    file = io.BytesIO(content)
    file.name = "test.log"
    result = read_uploaded_file(file)
    assert "something broke" in result
    assert "disk full" in result


def test_read_json_file():
    content = b'[{"level": "error", "msg": "OOM kill"}]'
    file = io.BytesIO(content)
    file.name = "test.json"
    result = read_uploaded_file(file)
    assert "OOM kill" in result


def test_read_csv_file():
    content = b"timestamp,level,message\n2024-01-15,ERROR,disk full"
    file = io.BytesIO(content)
    file.name = "test.csv"
    result = read_uploaded_file(file)
    assert "disk full" in result


def test_read_empty_file():
    file = io.BytesIO(b"")
    file.name = "empty.log"
    result = read_uploaded_file(file)
    assert result == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_log_parser.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'utils.log_parser'`

- [ ] **Step 3: Write the implementation**

Create `utils/log_parser.py`:

```python
import csv
import io
import json


def read_uploaded_file(file) -> str:
    """Read an uploaded file and return its contents as a string.

    Handles .log, .txt, .json, and .csv formats.
    """
    raw = file.read()
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")

    if not raw.strip():
        return ""

    name = getattr(file, "name", "")

    if name.endswith(".json"):
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return "\n".join(json.dumps(entry) for entry in data)
            return json.dumps(data)
        except json.JSONDecodeError:
            return raw

    if name.endswith(".csv"):
        reader = csv.DictReader(io.StringIO(raw))
        lines = []
        for row in reader:
            lines.append(" | ".join(f"{k}: {v}" for k, v in row.items()))
        return "\n".join(lines)

    # .log, .txt, or unknown — return as-is
    return raw
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_log_parser.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add utils/log_parser.py tests/test_log_parser.py
git commit -m "feat: add log file parser utility for multi-format support"
```

---

### Task 11: Sample Log Files

**Files:**
- Create: `sample_logs/mixed_incident.log`
- Create: `sample_logs/k8s_crash.json`
- Create: `sample_logs/app_errors.csv`

- [ ] **Step 1: Create mixed_incident.log**

```
2024-01-15 03:42:18 ERROR kernel: [42819.234] Out of memory: Killed process 1842 (node) total-vm:2451832kB, anon-rss:2097152kB, file-rss:0kB
2024-01-15 03:42:18 CRITICAL systemd: api-server.service: Main process exited, code=killed, status=9/KILL
2024-01-15 03:42:19 ERROR kubelet: Pod api-server-7f8d9b6c4-xj2k9 container exceeded memory limit (2Gi), OOMKilled
2024-01-15 03:42:20 WARN sqlalchemy.pool: QueuePool limit of 20 overflow 10 reached, connection timed out after 30s
2024-01-15 03:42:20 ERROR sqlalchemy.exc.TimeoutError: QueuePool limit of 20 overflow 10 reached, connection timed out, timeout 30.00
2024-01-15 03:42:25 WARN db.connection: Retry attempt 1/3 for database connection to primary-db:5432
2024-01-15 03:42:30 ERROR db.connection: All retry attempts exhausted for primary-db:5432
2024-01-15 03:43:01 ERROR auth.middleware: JWT validation failed for /api/v2/users: token expired at 1705283000
2024-01-15 03:43:01 WARN auth.middleware: 15 consecutive auth failures from IP 10.0.3.42 in last 60s
2024-01-15 03:43:05 ERROR nginx: upstream timed out (110: Connection timed out) while reading response header from upstream, client: 10.0.3.42
2024-01-15 03:43:10 WARN disk.monitor: /dev/sda1 usage at 92%, threshold is 85%
2024-01-15 03:43:15 INFO app.healthcheck: Health check failed for service payment-gateway, status=503
2024-01-15 03:43:20 ERROR network.dns: DNS resolution failed for internal-api.cluster.local, NXDOMAIN
2024-01-15 03:43:25 WARN config.loader: Deprecated config key 'db_pool_size' used, migrate to 'database.pool.size'
2024-01-15 03:43:30 ERROR cron.scheduler: Scheduled job cleanup_temp_files failed: PermissionError: [Errno 13] Permission denied: '/tmp/app-cache'
```

- [ ] **Step 2: Create k8s_crash.json**

```json
[
  {"timestamp": "2024-01-15T03:42:18Z", "level": "error", "component": "kubelet", "pod": "api-server-7f8d9b6c4-xj2k9", "namespace": "production", "message": "Container OOMKilled", "reason": "OOMKilled", "exitCode": 137, "restartCount": 5},
  {"timestamp": "2024-01-15T03:42:19Z", "level": "warning", "component": "kubelet", "pod": "api-server-7f8d9b6c4-xj2k9", "namespace": "production", "message": "Back-off restarting failed container", "reason": "CrashLoopBackOff", "restartCount": 5},
  {"timestamp": "2024-01-15T03:42:25Z", "level": "error", "component": "scheduler", "pod": "worker-batch-9c7f3a2-m4k8", "namespace": "production", "message": "Failed to schedule pod: insufficient memory", "reason": "FailedScheduling", "availableMemory": "512Mi", "requestedMemory": "2Gi"},
  {"timestamp": "2024-01-15T03:42:30Z", "level": "error", "component": "kubelet", "pod": "redis-cache-0", "namespace": "production", "message": "Liveness probe failed: connection refused", "reason": "Unhealthy", "probeType": "liveness", "failureCount": 3},
  {"timestamp": "2024-01-15T03:42:35Z", "level": "warning", "component": "endpoint-controller", "service": "api-gateway", "namespace": "production", "message": "No ready endpoints for service", "readyEndpoints": 0, "totalEndpoints": 3},
  {"timestamp": "2024-01-15T03:42:40Z", "level": "error", "component": "ingress-controller", "namespace": "production", "message": "Upstream connection timeout", "backend": "api-gateway:8080", "timeout": "60s", "statusCode": 504}
]
```

- [ ] **Step 3: Create app_errors.csv**

```csv
timestamp,level,service,error_type,message,request_id,user_id
2024-01-15T03:42:18Z,ERROR,payment-service,ConnectionError,Failed to connect to payment gateway: timeout after 30s,req-a1b2c3,user-1001
2024-01-15T03:42:20Z,ERROR,payment-service,ConnectionError,Failed to connect to payment gateway: timeout after 30s,req-d4e5f6,user-1002
2024-01-15T03:42:22Z,ERROR,user-service,DatabaseError,deadlock detected: Process 4523 waits for ShareLock on transaction 98712,req-g7h8i9,user-1003
2024-01-15T03:42:25Z,WARN,auth-service,RateLimitExceeded,Rate limit exceeded for IP 10.0.3.42: 100 requests/min,req-j1k2l3,
2024-01-15T03:42:28Z,ERROR,notification-service,SMTPError,Failed to send email: Connection refused to smtp.internal:587,req-m4n5o6,user-1004
2024-01-15T03:42:30Z,ERROR,inventory-service,CacheError,Redis connection lost: ECONNRESET,req-p7q8r9,
2024-01-15T03:42:35Z,WARN,api-gateway,CircuitBreakerOpen,Circuit breaker open for payment-service: 5 failures in 60s,req-s1t2u3,user-1005
2024-01-15T03:42:40Z,ERROR,order-service,ValidationError,Order total mismatch: calculated=99.99 submitted=0.01,req-v4w5x6,user-1006
```

- [ ] **Step 4: Commit**

```bash
git add sample_logs/
git commit -m "feat: add sample log files for demo (mixed, k8s, csv)"
```

---

### Task 12: Dark Theme CSS

**Files:**
- Create: `ui/theme.css`

- [ ] **Step 1: Create theme.css**

```css
/* Dark theme inspired by New Relic / GitHub Dark */
[data-testid="stAppViewContainer"] {
    background-color: #0d1117;
    color: #c9d1d9;
}

[data-testid="stSidebar"] {
    background-color: #161b22;
    border-right: 1px solid #30363d;
}

[data-testid="stHeader"] {
    background-color: #0d1117;
}

.stTabs [data-baseweb="tab-list"] {
    background-color: #161b22;
    border-bottom: 1px solid #30363d;
    gap: 0;
}

.stTabs [data-baseweb="tab"] {
    color: #8b949e;
    padding: 10px 20px;
}

.stTabs [aria-selected="true"] {
    color: #58a6ff;
    border-bottom: 2px solid #58a6ff;
}

/* Severity badges */
.severity-critical {
    background: #f8514933;
    color: #f85149;
    border-left: 3px solid #f85149;
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 10px;
}

.severity-high {
    background: #d2992233;
    color: #d29922;
    border-left: 3px solid #d29922;
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 10px;
}

.severity-medium {
    background: #58a6ff33;
    color: #58a6ff;
    border-left: 3px solid #58a6ff;
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 10px;
}

.severity-low {
    background: #484f5833;
    color: #8b949e;
    border-left: 3px solid #484f58;
    padding: 12px;
    border-radius: 6px;
    margin-bottom: 10px;
}

/* Log card */
.log-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 12px;
    margin-bottom: 10px;
}

.log-card code {
    background: #0d1117;
    padding: 6px 8px;
    border-radius: 4px;
    font-size: 12px;
    color: #8b949e;
    display: block;
    margin-top: 6px;
}

/* Trace bar */
.trace-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    overflow-x: auto;
}

.trace-node {
    padding: 6px 14px;
    border-radius: 4px;
    font-size: 12px;
    white-space: nowrap;
}

.trace-node-completed {
    background: #238636;
    color: white;
}

.trace-node-running {
    background: #1f6feb;
    color: white;
}

.trace-node-skipped {
    background: #30363d;
    color: #8b949e;
}

.trace-arrow {
    color: #30363d;
    font-size: 16px;
}

/* Remediation card */
.remediation-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
}

.confidence-bar {
    height: 4px;
    border-radius: 2px;
    background: #30363d;
    margin-top: 8px;
}

.confidence-fill {
    height: 100%;
    border-radius: 2px;
    background: #238636;
}

/* JIRA ticket card */
.jira-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    border-left: 4px solid #58a6ff;
}

.jira-label {
    display: inline-block;
    background: #30363d;
    color: #c9d1d9;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    margin-right: 4px;
}

/* Category tags */
.category-tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    margin: 2px;
}
```

- [ ] **Step 2: Commit**

```bash
git add ui/theme.css
git commit -m "feat: add dark theme CSS for Streamlit dashboard"
```

---

### Task 13: Streamlit UI Components

**Files:**
- Create: `ui/components.py`

- [ ] **Step 1: Create components.py**

```python
import streamlit as st
from pathlib import Path

SEVERITY_COLORS = {
    "CRITICAL": ("#f85149", "critical"),
    "HIGH": ("#d29922", "high"),
    "MEDIUM": ("#58a6ff", "medium"),
    "LOW": ("#8b949e", "low"),
}

SEVERITY_EMOJI = {
    "CRITICAL": "\U0001f534",
    "HIGH": "\U0001f7e0",
    "MEDIUM": "\U0001f535",
    "LOW": "\u26aa",
}


def inject_theme():
    css_path = Path(__file__).parent / "theme.css"
    css = css_path.read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def severity_badge(severity: str) -> str:
    color, _ = SEVERITY_COLORS.get(severity, ("#8b949e", "low"))
    return (
        f'<span style="background:{color}33; color:{color}; '
        f'padding:2px 8px; border-radius:10px; font-size:12px; '
        f'font-weight:bold;">{severity}</span>'
    )


def log_card(entry: dict):
    severity = entry.get("severity", "LOW")
    _, css_class = SEVERITY_COLORS.get(severity, ("#8b949e", "low"))
    st.markdown(
        f"""<div class="severity-{css_class}">
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                {severity_badge(severity)}
                <span style="color:#484f58; font-size:12px;">{entry.get('timestamp', '')}</span>
            </div>
            <div style="color:#c9d1d9; font-size:14px; margin-bottom:4px;">
                <strong>{entry.get('category', '')}</strong> — {entry.get('summary', '')}
            </div>
            <code>{entry.get('raw_line', '')}</code>
        </div>""",
        unsafe_allow_html=True,
    )


def remediation_card(rem: dict):
    confidence = rem.get("confidence", 0)
    pct = int(confidence * 100)
    steps_html = "".join(f"<li>{step}</li>" for step in rem.get("fix_steps", []))
    st.markdown(
        f"""<div class="remediation-card">
            <h4 style="color:#c9d1d9; margin:0 0 8px 0;">{rem.get('issue_summary', '')}</h4>
            <p style="color:#8b949e; font-size:13px;"><strong>Root cause:</strong> {rem.get('root_cause', '')}</p>
            <p style="color:#8b949e; font-size:13px;"><strong>Rationale:</strong> {rem.get('rationale', '')}</p>
            <p style="color:#c9d1d9; font-size:13px;"><strong>Fix steps:</strong></p>
            <ol style="color:#c9d1d9; font-size:13px;">{steps_html}</ol>
            <div style="display:flex; align-items:center; gap:8px; margin-top:8px;">
                <span style="color:#8b949e; font-size:12px;">Confidence: {pct}%</span>
                <div class="confidence-bar" style="flex:1;">
                    <div class="confidence-fill" style="width:{pct}%;"></div>
                </div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )


def jira_card(ticket: dict):
    labels_html = "".join(
        f'<span class="jira-label">{label}</span>' for label in ticket.get("labels", [])
    )
    st.markdown(
        f"""<div class="jira-card">
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <h4 style="color:#c9d1d9; margin:0;">{ticket.get('title', '')}</h4>
                <span style="color:#58a6ff; font-size:12px;">{ticket.get('priority', '')}</span>
            </div>
            <p style="color:#8b949e; font-size:13px;">{ticket.get('description', '')}</p>
            <div style="margin-top:8px;">
                <span style="color:#8b949e; font-size:11px;">Assignee: {ticket.get('assignee', 'Unassigned')}</span>
            </div>
            <div style="margin-top:6px;">{labels_html}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def trace_bar(trace_entries: list[dict]):
    if not trace_entries:
        st.info("No agent trace data yet.")
        return

    nodes_html = ""
    for i, entry in enumerate(trace_entries):
        status = entry.get("status", "pending")
        css_class = f"trace-node-{status}" if status in ("completed", "running", "skipped") else "trace-node-skipped"
        duration = entry.get("end_time", 0) - entry.get("start_time", 0)
        icon = {"completed": "\u2705", "running": "\u2699\ufe0f", "skipped": "\u26aa", "failed": "\u274c"}.get(status, "\u26aa")

        nodes_html += f'<div class="trace-node {css_class}">{icon} {entry["agent_name"]}<br><span style="font-size:10px; opacity:0.7;">{duration:.1f}s</span></div>'
        if i < len(trace_entries) - 1:
            nodes_html += '<div class="trace-arrow">\u27a1</div>'

    st.markdown(f'<div class="trace-bar">{nodes_html}</div>', unsafe_allow_html=True)


def severity_summary(entries: list[dict]):
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for entry in entries:
        sev = entry.get("severity", "LOW")
        if sev in counts:
            counts[sev] += 1

    for sev, count in counts.items():
        emoji = SEVERITY_EMOJI[sev]
        color, _ = SEVERITY_COLORS[sev]
        st.markdown(
            f'<div style="display:flex; justify-content:space-between; padding:4px 0;">'
            f'<span>{emoji} <span style="color:#c9d1d9;">{sev.title()}</span></span>'
            f'<span style="color:{color}; font-weight:bold; font-size:16px;">{count}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


def category_tags(entries: list[dict]):
    categories = {}
    for entry in entries:
        cat = entry.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    tags_html = ""
    for cat, count in categories.items():
        tags_html += f'<span class="category-tag" style="background:#30363d; color:#c9d1d9;">{cat} ({count})</span>'

    st.markdown(f'<div>{tags_html}</div>', unsafe_allow_html=True)
```

- [ ] **Step 2: Commit**

```bash
git add ui/components.py
git commit -m "feat: add Streamlit UI components for dashboard"
```

---

### Task 14: Streamlit Tab Renderers

**Files:**
- Create: `ui/tabs.py`

- [ ] **Step 1: Create tabs.py**

```python
import streamlit as st
from ui.components import log_card, remediation_card, jira_card, trace_bar


def render_analysis_tab(state: dict):
    entries = state.get("classified_entries", [])
    if not entries:
        st.info("No classified entries yet. Upload logs and run analysis.")
        return

    st.markdown(f"**{len(entries)} log entries classified**")
    for entry in entries:
        log_card(entry)


def render_remediations_tab(state: dict):
    remediations = state.get("remediations", [])
    if not remediations:
        st.info("No remediations generated yet.")
        return

    st.markdown(f"**{len(remediations)} remediations generated**")
    for rem in remediations:
        remediation_card(rem)


def render_cookbook_tab(state: dict):
    cookbook = state.get("cookbook", "")
    if not cookbook:
        st.info("No cookbook generated yet.")
        return

    st.markdown(cookbook)


def render_slack_tab(state: dict):
    notifications = state.get("slack_notifications", [])
    if not notifications:
        st.info("No Slack notifications sent yet.")
        return

    for notif in notifications:
        status_icon = "\u2705" if notif["status"] == "sent" else "\u274c"
        st.markdown(
            f"""<div style="background:#161b22; border:1px solid #30363d; border-radius:8px; padding:12px; margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:#c9d1d9;">{status_icon} {notif['channel']}</span>
                    <span style="color:#8b949e; font-size:12px;">{notif['status']}</span>
                </div>
                <p style="color:#8b949e; font-size:13px; margin-top:6px;">{notif['text']}</p>
            </div>""",
            unsafe_allow_html=True,
        )


def render_jira_tab(state: dict):
    tickets = state.get("jira_tickets", [])
    if not tickets:
        st.info("No JIRA tickets created.")
        return

    st.markdown(
        '<p style="color:#8b949e; font-size:12px; margin-bottom:12px;">'
        '\u2139\ufe0f These tickets are mocked — no real JIRA API calls were made.</p>',
        unsafe_allow_html=True,
    )
    for ticket in tickets:
        jira_card(ticket)


def render_trace_tab(state: dict):
    traces = state.get("agent_trace", [])
    if not traces:
        st.info("No agent trace data yet.")
        return

    # Timeline view
    st.subheader("Execution Timeline")
    trace_bar(traces)

    # Detail view
    st.subheader("Agent Details")
    for trace in traces:
        status_icon = {"completed": "\u2705", "running": "\u2699\ufe0f", "skipped": "\u26aa", "failed": "\u274c"}.get(
            trace["status"], "\u26aa"
        )
        duration = trace.get("end_time", 0) - trace.get("start_time", 0)
        with st.expander(f"{status_icon} {trace['agent_name']} — {duration:.1f}s"):
            st.markdown(f"**Status:** {trace['status']}")
            st.markdown(f"**Duration:** {duration:.1f}s")
            st.markdown(f"**Input:** {trace.get('input_summary', 'N/A')}")
            st.markdown(f"**Output:** {trace.get('output_summary', 'N/A')}")
```

- [ ] **Step 2: Commit**

```bash
git add ui/tabs.py
git commit -m "feat: add tab renderers for all 6 dashboard tabs"
```

---

### Task 15: Streamlit App Entry Point

**Files:**
- Create: `app.py`

- [ ] **Step 1: Create app.py**

```python
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from orchestrator.graph import build_graph
from orchestrator.state import make_initial_state
from utils.log_parser import read_uploaded_file
from ui.components import inject_theme, severity_summary, category_tags, trace_bar
from ui.tabs import (
    render_analysis_tab,
    render_remediations_tab,
    render_cookbook_tab,
    render_slack_tab,
    render_jira_tab,
    render_trace_tab,
)

st.set_page_config(
    page_title="DevOps Incident Analyzer",
    page_icon="\U0001f6e1\ufe0f",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()

# Initialize session state
if "analysis_state" not in st.session_state:
    st.session_state.analysis_state = None
if "is_running" not in st.session_state:
    st.session_state.is_running = False

# --- Sidebar ---
with st.sidebar:
    st.markdown("### \U0001f6e1\ufe0f Incident Analyzer")
    st.markdown('<span style="color:#8b949e; font-size:12px;">Multi-Agent DevOps Suite</span>', unsafe_allow_html=True)
    st.divider()

    # Log input section
    st.markdown("**Log Input**")
    uploaded_file = st.file_uploader(
        "Upload log file",
        type=["log", "txt", "json", "csv"],
        help="Supports .log, .txt, .json, .csv formats",
    )

    pasted_logs = st.text_area(
        "Or paste logs here",
        height=150,
        placeholder="Paste log content...",
    )

    analyze_button = st.button(
        "\u25b6\ufe0f Analyze Logs",
        use_container_width=True,
        disabled=st.session_state.is_running,
    )

    # Severity summary (after analysis)
    if st.session_state.analysis_state:
        st.divider()
        st.markdown("**Severity Breakdown**")
        severity_summary(st.session_state.analysis_state.get("classified_entries", []))

        st.divider()
        st.markdown("**Issue Categories**")
        category_tags(st.session_state.analysis_state.get("classified_entries", []))

# --- Main Content ---
st.markdown(
    '<h1 style="color:#58a6ff; margin-bottom:0;">\U0001f6e1\ufe0f DevOps Incident Analyzer</h1>'
    '<p style="color:#8b949e;">Multi-Agent Analysis Suite</p>',
    unsafe_allow_html=True,
)

# Handle analysis
if analyze_button:
    raw_logs = ""
    if uploaded_file is not None:
        raw_logs = read_uploaded_file(uploaded_file)
    elif pasted_logs.strip():
        raw_logs = pasted_logs.strip()

    if not raw_logs:
        st.error("Please upload a file or paste log content.")
    else:
        st.session_state.is_running = True
        with st.spinner("Analyzing logs with multi-agent pipeline..."):
            graph = build_graph()
            initial_state = make_initial_state(raw_logs)
            result = graph.invoke(initial_state)
            st.session_state.analysis_state = result
        st.session_state.is_running = False
        st.rerun()

# Display results
if st.session_state.analysis_state:
    # Agent trace bar at top
    st.markdown("---")
    st.markdown("**Agent Execution Trace**")
    trace_bar(st.session_state.analysis_state.get("agent_trace", []))
    st.markdown("---")

    # Tabs
    tab_analysis, tab_remediations, tab_cookbook, tab_slack, tab_jira, tab_trace = st.tabs(
        [
            "\U0001f50d Analysis",
            "\U0001f527 Remediations",
            "\U0001f4d6 Cookbook",
            "\U0001f4ac Slack Log",
            "\U0001f3ab JIRA Tickets",
            "\U0001f500 Agent Trace",
        ]
    )

    with tab_analysis:
        render_analysis_tab(st.session_state.analysis_state)
    with tab_remediations:
        render_remediations_tab(st.session_state.analysis_state)
    with tab_cookbook:
        render_cookbook_tab(st.session_state.analysis_state)
    with tab_slack:
        render_slack_tab(st.session_state.analysis_state)
    with tab_jira:
        render_jira_tab(st.session_state.analysis_state)
    with tab_trace:
        render_trace_tab(st.session_state.analysis_state)
else:
    st.markdown(
        """<div style="display:flex; align-items:center; justify-content:center; min-height:400px;">
            <div style="text-align:center;">
                <p style="font-size:48px; margin-bottom:8px;">\U0001f4cb</p>
                <h3 style="color:#c9d1d9;">Upload or paste ops logs to get started</h3>
                <p style="color:#8b949e;">The multi-agent pipeline will classify issues, generate remediations, and push notifications.</p>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
```

- [ ] **Step 2: Test the app starts**

Run: `streamlit run app.py --server.headless true`
Expected: App starts without import errors. Visit http://localhost:8501 and see the dashboard with empty state.

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: add Streamlit dashboard entry point with all tabs"
```

---

### Task 16: End-to-End Smoke Test

**Files:**
- Modify: `tests/test_graph.py`

- [ ] **Step 1: Add an integration test with sample logs**

Add to `tests/test_graph.py`:

```python
@patch("agents.jira_ticket.ChatOpenAI")
@patch("agents.slack_notifier.WebClient")
@patch("agents.cookbook.ChatOpenAI")
@patch("agents.remediation.ChatOpenAI")
@patch("agents.classifier.ChatOpenAI")
def test_graph_with_low_severity_skips_jira_and_slack(
    mock_classifier_llm,
    mock_remediation_llm,
    mock_cookbook_llm,
    mock_slack_client,
    mock_jira_llm,
):
    low_classified = [
        {
            "timestamp": "2024-01-15T03:43:25Z",
            "severity": "LOW",
            "category": "config",
            "source": "config.loader",
            "raw_line": "Deprecated config key used",
            "summary": "Deprecated config key",
        },
    ]
    low_remediations = [
        {
            "issue_summary": "Deprecated config",
            "root_cause": "Old config key",
            "fix_steps": ["Update config key"],
            "rationale": "Non-breaking",
            "confidence": 0.95,
            "linked_log_entries": [0],
        },
    ]

    mock_cls = MagicMock()
    mock_cls.invoke.return_value = MagicMock(content=json.dumps(low_classified))
    mock_classifier_llm.return_value = mock_cls

    mock_rem = MagicMock()
    mock_rem.invoke.return_value = MagicMock(content=json.dumps(low_remediations))
    mock_remediation_llm.return_value = mock_rem

    mock_cb = MagicMock()
    mock_cb.invoke.return_value = MagicMock(content="# Low priority runbook")
    mock_cookbook_llm.return_value = mock_cb

    graph = build_graph()
    initial_state = make_initial_state("2024-01-15 WARN Deprecated config key used")

    with patch.dict("os.environ", {"SLACK_BOT_TOKEN": "xoxb-test", "SLACK_CHANNEL": "#test"}):
        result = graph.invoke(initial_state)

    assert len(result["classified_entries"]) == 1
    assert len(result["remediations"]) == 1
    assert "runbook" in result["cookbook"].lower()
    # LOW severity → no JIRA, no Slack
    assert result["jira_tickets"] == []
    assert result["slack_notifications"] == []
```

- [ ] **Step 2: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_graph.py
git commit -m "test: add end-to-end smoke test for low-severity routing"
```

---

### Task 17: Final Verification & Cleanup

- [ ] **Step 1: Run the full test suite**

Run: `pytest tests/ -v --tb=short`
Expected: All tests PASS. No warnings about missing modules.

- [ ] **Step 2: Verify the app runs**

Run: `streamlit run app.py --server.headless true`
Expected: App starts at http://localhost:8501. Upload `sample_logs/mixed_incident.log` and verify the full pipeline runs (requires real `OPENAI_API_KEY` in `.env`).

- [ ] **Step 3: Verify project structure is complete**

Run: `find . -name "*.py" -not -path "./.git/*" | sort`
Expected output:
```
./agents/__init__.py
./agents/classifier.py
./agents/cookbook.py
./agents/jira_ticket.py
./agents/remediation.py
./agents/slack_notifier.py
./app.py
./orchestrator/__init__.py
./orchestrator/graph.py
./orchestrator/router.py
./orchestrator/state.py
./tests/__init__.py
./tests/test_classifier.py
./tests/test_cookbook.py
./tests/test_graph.py
./tests/test_jira.py
./tests/test_log_parser.py
./tests/test_remediation.py
./tests/test_router.py
./tests/test_slack.py
./tests/test_state.py
./ui/__init__.py
./ui/components.py
./ui/tabs.py
./utils/__init__.py
./utils/log_parser.py
./utils/slack_client.py
```

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "chore: final verification — all tests passing, project structure complete"
```
