import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from utils.helpers import SLACK_BOT_TOKEN, SLACK_CHANNEL_ID, MOCK_MODE

client = WebClient(token=SLACK_BOT_TOKEN)

def send_slack_notification(classified_logs: dict, remediation: dict) -> dict:
    summary = classified_logs.get("summary", "No summary available")
    issues = classified_logs.get("issues", [])
    remediations = remediation.get("remediations", [])

    critical_issues = [i for i in issues if i.get("severity") == "CRITICAL"]
    high_issues = [i for i in issues if i.get("severity") == "HIGH"]

    message_blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🚨 DevOps Incident Alert"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Summary:*\n{summary}"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Total Issues:*\n{len(issues)}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Critical:*\n{len(critical_issues)}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*High:*\n{len(high_issues)}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Services Affected:*\n{len(classified_logs.get('affected_services', []))}"
                }
            ]
        },
        {
            "type": "divider"
        }
    ]

    for rem in remediations[:3]:
        message_blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{rem.get('severity')} — {rem.get('title')}*\n"
                        f"*Immediate Action:* {rem.get('immediate_action')}\n"
                        f"*ETA:* {rem.get('estimated_time')}"
            }
        })

    message_text = f"🚨 Incident Alert: {summary}"

    if MOCK_MODE:
        return {
            "status": "mocked",
            "message": message_text,
            "blocks": message_blocks,
            "channel": SLACK_CHANNEL_ID
        }

    try:
        response = client.chat_postMessage(
            channel=SLACK_CHANNEL_ID,
            text=message_text,
            blocks=message_blocks
        )
        return {
            "status": "sent",
            "message": message_text,
            "blocks": message_blocks,
            "ts": response["ts"],
            "channel": response["channel"]
        }
    except SlackApiError as e:
        return {
            "status": "error",
            "error": str(e),
            "message": message_text,
            "blocks": message_blocks
        }