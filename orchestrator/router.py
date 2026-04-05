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
