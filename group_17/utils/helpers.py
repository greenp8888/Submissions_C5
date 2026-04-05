import os
from dotenv import load_dotenv

load_dotenv()

def get_env(key):
    val = os.getenv(key)
    if not val:
        raise ValueError(f"Missing environment variable: {key}")
    return val

ANTHROPIC_API_KEY = get_env("ANTHROPIC_API_KEY")
SLACK_BOT_TOKEN = get_env("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = get_env("SLACK_CHANNEL_ID")
JIRA_SERVER = get_env("JIRA_SERVER")
JIRA_EMAIL = get_env("JIRA_EMAIL")
JIRA_API_TOKEN = get_env("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = get_env("JIRA_PROJECT_KEY")
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"