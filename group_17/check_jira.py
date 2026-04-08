from jira import JIRA
import os
from dotenv import load_dotenv

load_dotenv()

jira = JIRA(
    server=os.getenv("JIRA_SERVER"),
    basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN"))
)

project = jira.project("SCRUM")
issue_types = jira.issue_types()

print("Available issue types:")
for it in issue_types:
    print(f"  - {it.name}")