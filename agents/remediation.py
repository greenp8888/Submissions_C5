import json
import time
from langchain_core.messages import SystemMessage, HumanMessage
from orchestrator.state import IncidentState
from utils.llm import get_llm

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

    llm = get_llm()
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
        "agent_trace": [trace_entry],
    }
