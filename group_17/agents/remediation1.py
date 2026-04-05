import anthropic
import json
from utils.helpers import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def generate_remediation(classified_logs: dict) -> dict:
    issues_text = json.dumps(classified_logs.get("issues", []), indent=2)
    
    prompt = f"""You are an expert DevOps Site Reliability Engineer (SRE).

Based on these detected issues, provide detailed remediation steps for each:

ISSUES FOUND:
{issues_text}

AFFECTED SERVICES: {', '.join(classified_logs.get('affected_services', []))}

For each issue provide:
1. Immediate fix (what to do RIGHT NOW)
2. Root cause explanation
3. Step by step remediation commands
4. Prevention steps for future

Return in this exact JSON format:
{{
    "remediations": [
        {{
            "issue_id": "ISSUE-1",
            "severity": "CRITICAL",
            "title": "issue title",
            "root_cause": "explanation of why this happened",
            "immediate_action": "what to do right now",
            "steps": [
                "Step 1: specific command or action",
                "Step 2: specific command or action",
                "Step 3: verify the fix"
            ],
            "commands": [
                "kubectl rollout restart deployment/service-name",
                "systemctl restart nginx"
            ],
            "prevention": "how to prevent this in future",
            "estimated_time": "5 minutes"
        }}
    ],
    "priority_order": ["ISSUE-1", "ISSUE-2"],
    "overall_recommendation": "high level recommendation"
}}

DETECTED ISSUES:
{issues_text}
"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text

    try:
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        json_str = response_text[start:end]
        return json.loads(json_str)
    except:
        return {
            "remediations": [],
            "priority_order": [],
            "overall_recommendation": response_text
        }