from jira import JIRA
from jira.exceptions import JIRAError

from incident_suite.models.schemas import ExternalActionResult
from incident_suite.utils.settings import get_settings


def create_issue(
    summary: str,
    description: str,
    priority: str,
    base_url: str | None = None,
    email: str | None = None,
    api_token: str | None = None,
    project_key: str | None = None,
) -> ExternalActionResult:
    settings = get_settings()
    resolved_base_url = base_url or settings.jira_base_url
    resolved_email = email or settings.jira_email
    resolved_api_token = api_token or settings.jira_api_token
    required = [resolved_base_url, resolved_email, resolved_api_token]
    if not all(required):
        return ExternalActionResult(success=False, message="Jira is not configured.")

    try:
        client = JIRA(server=resolved_base_url, basic_auth=(resolved_email, resolved_api_token))
        issue = client.create_issue(
            fields={
                "project": {"key": project_key or settings.jira_project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": settings.jira_issue_type},
                "priority": {"name": priority.title()},
            }
        )
        return ExternalActionResult(
            success=True,
            external_id=issue.key,
            url=f"{resolved_base_url}/browse/{issue.key}",
            message="Jira issue created.",
        )
    except JIRAError as exc:
        return ExternalActionResult(success=False, message=f"Jira issue creation failed: {exc.text or str(exc)}")
    except Exception as exc:
        return ExternalActionResult(success=False, message=f"Jira issue creation failed: {exc}")
