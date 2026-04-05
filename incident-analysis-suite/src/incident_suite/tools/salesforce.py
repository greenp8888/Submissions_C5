import httpx
from simple_salesforce import Salesforce

from incident_suite.models.schemas import ExternalActionResult
from incident_suite.utils.settings import get_settings


def _normalize_instance_url(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""
    if cleaned.startswith(("http://", "https://")):
        return cleaned.rstrip("/")
    return f"https://{cleaned.rstrip('/')}"


def upsert_incident_case(
    subject: str,
    description: str,
    priority: str,
    instance_url: str | None = None,
    access_token: str | None = None,
) -> ExternalActionResult:
    settings = get_settings()
    runtime_instance_url = _normalize_instance_url(instance_url or settings.salesforce_instance_url)
    runtime_access_token = (access_token or "").strip()
    if runtime_instance_url and runtime_access_token:
        try:
            payload = {
                "Subject": subject,
                "Description": description,
                "Priority": priority.title(),
                "Origin": "AI Incident Suite",
                "Status": "New",
            }
            response = httpx.post(
                f"{runtime_instance_url}/services/data/v61.0/sobjects/{settings.salesforce_incident_object}/",
                headers={
                    "Authorization": f"Bearer {runtime_access_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=30.0,
            )
            data = response.json()
            response.raise_for_status()
            return ExternalActionResult(
                success=True,
                external_id=data.get("id"),
                url=f"{runtime_instance_url}/{data.get('id')}" if data.get("id") else None,
                message="Salesforce incident created with bearer token.",
            )
        except Exception as exc:
            return ExternalActionResult(success=False, message=f"Salesforce incident sync failed: {exc}")

    required = [settings.salesforce_username, settings.salesforce_password, settings.salesforce_security_token]
    if not all(required):
        return ExternalActionResult(success=False, message="Salesforce is not configured.")

    try:
        sf = Salesforce(
            username=settings.salesforce_username,
            password=settings.salesforce_password,
            security_token=settings.salesforce_security_token,
            domain=settings.salesforce_domain,
        )
        payload = {
            "Subject": subject,
            "Description": description,
            "Priority": priority.title(),
            "Origin": "AI Incident Suite",
            "Status": "New",
        }
        result = getattr(sf, settings.salesforce_incident_object).create(payload)
        return ExternalActionResult(success=True, external_id=result.get("id"), message="Salesforce incident created.")
    except Exception as exc:
        return ExternalActionResult(success=False, message=f"Salesforce incident sync failed: {exc}")
