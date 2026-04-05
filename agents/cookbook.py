import json
import time
from langchain_core.messages import SystemMessage, HumanMessage
from orchestrator.state import IncidentState
from utils.llm import get_llm

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

    llm = get_llm()
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
        "agent_trace": [trace_entry],
    }
