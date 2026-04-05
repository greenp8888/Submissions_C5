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

    # Read from .env directly to avoid Streamlit env var issues
    from pathlib import Path
    from dotenv import dotenv_values
    env_path = Path(__file__).resolve().parent.parent / ".env"
    config = dotenv_values(env_path) if env_path.exists() else {}

    token = config.get("SLACK_BOT_TOKEN", "") or os.environ.get("SLACK_BOT_TOKEN", "")
    channel = config.get("SLACK_CHANNEL", "") or os.environ.get("SLACK_CHANNEL", "#incident-alerts")
    if not channel.startswith("#"):
        channel = f"#{channel}"
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
        "agent_trace": [trace_entry],
    }
