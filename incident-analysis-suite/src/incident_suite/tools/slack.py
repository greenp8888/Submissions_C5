import ssl
from urllib.error import URLError

import certifi
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from incident_suite.models.schemas import ExternalActionResult
from incident_suite.utils.settings import get_settings


def post_incident_message(
    summary: str,
    bot_token: str | None = None,
    channel_id: str | None = None,
) -> ExternalActionResult:
    settings = get_settings()
    resolved_bot_token = bot_token or settings.slack_bot_token
    resolved_channel_id = channel_id or settings.slack_default_channel_id
    if not resolved_bot_token or not resolved_channel_id:
        return ExternalActionResult(success=False, message="Slack is not configured.")

    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        client = WebClient(token=resolved_bot_token, ssl=ssl_context)
        response = client.chat_postMessage(channel=resolved_channel_id, text=summary)
        ts = response.get("ts")
        return ExternalActionResult(success=True, external_id=ts, message="Slack message sent.")
    except URLError as exc:
        return ExternalActionResult(
            success=False,
            message=f"Slack notification failed due to local SSL certificate verification: {exc}",
        )
    except SlackApiError as exc:
        error_message = exc.response.get("error") if exc.response else str(exc)
        return ExternalActionResult(success=False, message=f"Slack notification failed: {error_message}")
    except Exception as exc:
        return ExternalActionResult(success=False, message=f"Slack notification failed: {exc}")
