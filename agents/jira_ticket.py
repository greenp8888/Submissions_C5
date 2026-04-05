import json
import logging
import time
from langchain_core.messages import SystemMessage, HumanMessage
from orchestrator.state import IncidentState
from utils.llm import get_llm

logger = logging.getLogger(__name__)

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
    """Create JIRA ticket objects for CRITICAL and HIGH severity issues.

    Filters remediations linked to high-severity log entries and generates
    structured ticket data with title, description, priority, and labels.

    Args:
        state: Current incident state containing classified_entries and remediations.

    Returns:
        Dict with jira_tickets and agent_trace updates.
    """
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
        logger.warning("No CRITICAL/HIGH remediations found — skipping JIRA ticket creation")
        end_time = time.time()
        return {
            "jira_tickets": [],
            "agent_trace": [{
                "agent_name": "jira_ticket",
                "start_time": start_time,
                "end_time": end_time,
                "input_summary": "No critical/high remediations",
                "output_summary": "No tickets created",
                "status": "completed",
            }],
        }

    logger.info("Creating JIRA tickets for %d critical/high remediations", len(critical_remediations))

    llm = get_llm()
    remediations_json = json.dumps(critical_remediations, indent=2)
    messages = [
        SystemMessage(content=JIRA_SYSTEM_PROMPT),
        HumanMessage(content=f"Create JIRA tickets for these remediations:\n\n{remediations_json}"),
    ]
    response = llm.invoke(messages)

    raw_content = response.content.strip()
    if raw_content.startswith("```"):
        raw_content = raw_content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        tickets = json.loads(raw_content)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse jira_ticket JSON response: %s\nRaw content: %s", e, raw_content)
        raise

    end_time = time.time()
    logger.info("Created %d JIRA tickets in %.1fs", len(tickets), end_time - start_time)

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
        "agent_trace": [trace_entry],
    }
