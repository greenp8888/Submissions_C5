# Multi-Agent DevOps Incident Analysis Suite — Design Spec

## Overview

A multi-agent application that analyzes uploaded ops logs, classifies issues by severity, generates remediations, and pushes actionable output to Slack and JIRA. Built for a 1-day hackathon by a team of 4-5 Python developers.

**Goal:** Demonstrate multi-agent orchestration, automated remediation, and cross-tool notification in a scalable DevOps workflow.

**Reference:** Inspired by New Relic's incident analysis capabilities.

## Architecture

**Pattern:** Hub-and-Spoke — a central LangGraph orchestrator dynamically decides which agents to invoke based on log content and severity.

```
                         ┌──────────────┐
                         │  Streamlit UI │
                         │  (Dashboard)  │
                         └──────┬───────┘
                                │ upload logs / paste
                                ▼
                      ┌──────────────────┐
                      │   Orchestrator   │
                      │   (LangGraph)    │
                      │                  │
                      │  Shared State:   │
                      │  IncidentState   │
                      └──────┬──────────┘
                             │ decides next agent
               ┌─────────┬──┴───┬──────────┬───────────┐
               ▼         ▼      ▼          ▼           ▼
          ┌────────┐ ┌───────┐ ┌────────┐ ┌────────┐ ┌──────┐
          │  Log   │ │Remed- │ │Cook-   │ │ Slack  │ │ JIRA │
          │Classif.│ │iation │ │book    │ │ Notify │ │Ticket│
          │ Agent  │ │ Agent │ │Synth.  │ │ Agent  │ │Agent │
          └────────┘ └───────┘ └────────┘ └────────┘ └──────┘
```

### Orchestrator Routing Logic

1. **Always starts** with Log Classifier (needs classified data before anything else).
2. **After classification** — routes to Remediation Agent for all issues found.
3. **Conditional fan-out based on highest severity found across all classified entries:**
   - Any `CRITICAL/HIGH` present → Slack Notify + JIRA Ticket + Cookbook Synthesizer
   - Highest is `MEDIUM` → Slack Notify + Cookbook Synthesizer
   - All `LOW` → Cookbook Synthesizer only
   - All agents in the fan-out receive the full remediation list, not just entries matching the trigger severity.
4. **Completion** — all outputs aggregated, dashboard updated.

The orchestrator uses LangGraph conditional edges. After each agent completes, the orchestrator inspects the shared state to decide the next step.

## Shared State

```python
class LogEntry(TypedDict):
    timestamp: str
    severity: str          # CRITICAL, HIGH, MEDIUM, LOW
    category: str          # OOM, timeout, auth_failure, disk, network, etc.
    source: str
    raw_line: str
    summary: str

class Remediation(TypedDict):
    issue_summary: str
    root_cause: str
    fix_steps: list[str]
    rationale: str
    confidence: float
    linked_log_entries: list[int]  # indices into classified_entries

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
    status: str            # sent, failed

class TraceEntry(TypedDict):
    agent_name: str
    start_time: float
    end_time: float
    input_summary: str
    output_summary: str
    status: str            # running, completed, skipped, failed

class IncidentState(TypedDict):
    raw_logs: str
    classified_entries: list[LogEntry]
    remediations: list[Remediation]
    cookbook: str
    jira_tickets: list[JIRATicket]
    slack_notifications: list[SlackMessage]
    agent_trace: list[TraceEntry]
```

## Agent Specifications

### 1. Log Classifier Agent

- **Input:** `raw_logs` from state
- **Output:** `classified_entries: list[LogEntry]`
- **Behavior:** LLM parses unstructured logs of any format (syslog, JSON, CSV, plain text), extracts fields, classifies severity and category. Uses few-shot examples in the prompt to handle diverse formats. Batch processes all log lines in a single LLM call.

### 2. Remediation Agent

- **Input:** `classified_entries` from state
- **Output:** `remediations: list[Remediation]`
- **Behavior:** Groups related issues, maps each cluster to fix patterns. LLM reasons about root cause and generates actionable fix steps with confidence scores. Links each remediation back to the log entries that triggered it.

### 3. Cookbook Synthesizer Agent

- **Input:** `remediations` from state
- **Output:** `cookbook: str` (markdown)
- **Behavior:** Takes all remediations, deduplicates, prioritizes by severity, and produces an actionable incident response checklist as a markdown runbook. Groups steps by system/category.

### 4. Slack Notification Agent (Real Integration)

- **Input:** `remediations` + severity filter from state
- **Output:** `slack_notifications: list[SlackMessage]`
- **Behavior:** Formats remediations into Slack Block Kit messages with severity badges, fix summaries, and links. Posts to configured channel via `slack_sdk`. Records send status back to state.

### 5. JIRA Ticket Agent (Mocked)

- **Input:** `remediations` filtered to CRITICAL/HIGH severity
- **Output:** `jira_tickets: list[JIRATicket]`
- **Behavior:** Formats critical issues into JIRA-style ticket objects with title, description, priority, assignee, and labels. No real API call — returns structured data displayed in the dashboard.

## Dashboard (Streamlit)

### Layout

- **Left sidebar:** Log upload (file drag-drop + text paste), severity breakdown counters, issue category tags
- **Main content:** Tabbed view with 6 tabs
- **Bottom bar:** Agent execution trace with timing

### Tabs

1. **Analysis** — Classified log entries as cards, color-coded by severity (red=critical, orange=high, blue=medium, gray=low). Each card shows timestamp, severity, category, summary, raw log line.
2. **Remediations** — Fix cards with root cause, numbered fix steps, confidence score, linked log entries.
3. **Cookbook** — Rendered markdown runbook/checklist.
4. **Slack Log** — History of Slack notifications sent, with message previews and send status.
5. **JIRA Tickets** — Mocked ticket cards with title, priority, description, labels.
6. **Agent Trace** — Full execution graph showing agent flow, timing per node, inputs/outputs, LangGraph state at each step.

### Theme

Dark theme inspired by New Relic / GitHub dark. Custom CSS applied via Streamlit's theming and `st.markdown` with unsafe HTML.

## Tech Stack

| Component | Technology |
|---|---|
| LLM | GPT-4o via `langchain-openai` |
| Orchestration | LangGraph |
| UI | Streamlit |
| Slack | `slack-sdk` (real) |
| JIRA | Mocked (structured output only) |
| Config | `python-dotenv` |

## Project Structure

```
devops-incident-analyzer/
├── app.py                     # Streamlit entry point
├── requirements.txt
├── .env.example               # API keys template
├── agents/
│   ├── __init__.py
│   ├── classifier.py          # Log Classifier Agent
│   ├── remediation.py         # Remediation Agent
│   ├── cookbook.py             # Cookbook Synthesizer Agent
│   ├── slack_notifier.py      # Slack Notification Agent
│   └── jira_ticket.py         # JIRA Ticket Agent (mocked)
├── orchestrator/
│   ├── __init__.py
│   ├── graph.py               # LangGraph graph definition
│   ├── state.py               # TypedDict shared state
│   └── router.py              # Routing logic (severity-based)
├── ui/
│   ├── components.py          # Reusable Streamlit components
│   ├── tabs.py                # Tab renderers
│   └── theme.css              # Custom dark theme
├── utils/
│   ├── log_parser.py          # Pre-processing (file reading, format detection)
│   └── slack_client.py        # Slack SDK wrapper
└── sample_logs/               # Demo log files for presentation
    ├── mixed_incident.log
    ├── k8s_crash.json
    └── app_errors.csv
```

## Team Workstream Splits

### Person 1 — Orchestrator & Shared State (Critical Path)

- Define `IncidentState` TypedDict and all data models
- Build LangGraph graph with conditional edges
- Implement severity-based routing logic
- Wire agent trace capture (timing, inputs/outputs per node)
- Built first so others can plug their agents in

### Person 2 — Log Classifier + Remediation Agents

- Log Classifier: prompt engineering for multi-format parsing, `LogEntry` schema
- Remediation Agent: root cause reasoning, fix step generation
- Create sample log files for demo
- These two agents are tightly coupled — same person avoids interface mismatch

### Person 3 — Output Agents (Cookbook + Slack + JIRA)

- Cookbook Synthesizer: markdown checklist generation from remediations
- Slack Notifier: Block Kit formatting, `slack-sdk` integration, channel config
- JIRA mock: structured ticket output
- Simpler agents — one person handles all three

### Person 4 — Streamlit Dashboard

- Layout: sidebar, tabs, dark theme CSS
- All 6 tab renderers
- File upload + text paste input handling
- Real-time state display using `st.session_state`

### Person 5 — Integration & Demo Prep

- Wire orchestrator output into Streamlit via `st.session_state`
- Agent trace visualization (execution graph with timing)
- End-to-end testing with sample logs
- Demo script preparation, edge case handling

## Timeline (8-12 Hours)

| Phase | Hours | Activities |
|---|---|---|
| Setup | 0-1 | Repo, env, dependencies, Slack app created, state schema agreed |
| Parallel Build | 1-6 | Everyone builds their piece against agreed interfaces |
| Integration | 6-8 | Wire everything together, fix interface mismatches |
| Polish & Demo Prep | 8-10 | Dark theme, sample logs, agent trace view, demo script |
| Buffer | 10-12 | Bug fixes, rehearsal |

## Key Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Orchestrator routing gets complex | Pre-define routing rules as a simple severity→agents map, not open-ended LLM decisions |
| LLM hallucinations in log classification | Use structured output (JSON mode) + few-shot examples in prompts |
| Slack rate limits during demo | Pre-configure a dedicated demo channel, batch messages |
| Integration phase takes too long | Agree on TypedDict interfaces in hour 0, everyone codes to the contract |
| Streamlit limitations for complex dashboard | Use `st.markdown` with unsafe HTML for custom styling where needed |
