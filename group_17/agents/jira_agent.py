import json
from jira import JIRA
from utils.helpers import (
    JIRA_SERVER, JIRA_EMAIL,
    JIRA_API_TOKEN, JIRA_PROJECT_KEY, MOCK_MODE
)

def create_jira_tickets(classified_logs: dict, remediation: dict) -> dict:
    issues = classified_logs.get("issues", [])
    remediations = remediation.get("remediations", [])

    rem_map = {r.get("issue_id"): r for r in remediations}

    created_tickets = []

    if MOCK_MODE:
        for i, issue in enumerate(issues):
            rem = rem_map.get(issue.get("id"), {})
            ticket = {
                "status": "mocked",
                "ticket_id": f"SCRUM-{i+1}",
                "title": issue.get("title"),
                "severity": issue.get("severity"),
                "url": f"{JIRA_SERVER}/browse/SCRUM-{i+1}",
                "description": issue.get("description"),
                "immediate_action": rem.get("immediate_action", "N/A")
            }
            created_tickets.append(ticket)
        return {
            "status": "mocked",
            "tickets": created_tickets,
            "total_created": len(created_tickets)
        }

    try:
        jira = JIRA(
            server=JIRA_SERVER,
            basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN)
        )

        for issue in issues:
            rem = rem_map.get(issue.get("id"), {})

            severity = issue.get("severity", "MEDIUM")
            priority_map = {
                "CRITICAL": "Highest",
                "HIGH": "High",
                "MEDIUM": "Medium",
                "LOW": "Low"
            }

            steps_text = "\n".join(rem.get("steps", []))
            commands_text = "\n".join(rem.get("commands", []))

            description = f"""
*Incident Summary:*
{classified_logs.get('summary', 'N/A')}

*Issue Description:*
{issue.get('description', 'N/A')}

*Affected Service:*
{issue.get('affected_service', 'N/A')}

*Error Pattern:*
{issue.get('error_pattern', 'N/A')}

*Root Cause:*
{rem.get('root_cause', 'Under investigation')}

*Immediate Action Required:*
{rem.get('immediate_action', 'N/A')}

*Remediation Steps:*
{steps_text}

*Commands to Run:*
{{code}}
{commands_text}
{{code}}

*Prevention:*
{rem.get('prevention', 'N/A')}

*Estimated Resolution Time:*
{rem.get('estimated_time', 'Unknown')}
"""

            new_issue = jira.create_issue(
                project=JIRA_PROJECT_KEY,
                summary=f"[{severity}] {issue.get('title')}",
                description=description,
                issuetype={"name": "Task"},
                priority={"name": priority_map.get(severity, "Medium")}
            )

            created_tickets.append({
                "status": "created",
                "ticket_id": new_issue.key,
                "title": issue.get("title"),
                "severity": severity,
                "url": f"{JIRA_SERVER}/browse/{new_issue.key}",
                "description": issue.get("description"),
                "immediate_action": rem.get("immediate_action", "N/A")
            })

        return {
            "status": "success",
            "tickets": created_tickets,
            "total_created": len(created_tickets)
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "tickets": created_tickets,
            "total_created": len(created_tickets)
        }