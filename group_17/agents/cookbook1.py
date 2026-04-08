import anthropic
import json
from utils.helpers import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def generate_cookbook(classified_logs: dict, remediation: dict) -> dict:
    issues_text = json.dumps(classified_logs.get("issues", []), indent=2)
    remediation_text = json.dumps(remediation.get("remediations", []), indent=2)

    prompt = f"""You are a senior DevOps engineer creating a runbook/cookbook.

Based on the incident analysis and remediation steps, create a comprehensive 
actionable cookbook/runbook that can be used by any engineer to handle similar 
incidents in the future.

ISSUES DETECTED:
{issues_text}

REMEDIATION STEPS:
{remediation_text}

Create a detailed cookbook in this exact JSON format:
{{
    "title": "Incident Response Cookbook",
    "incident_type": "type of incident",
    "severity_level": "overall severity",
    "created_for": "brief description of what this cookbook addresses",
    "pre_checks": [
        "Check 1: what to verify first",
        "Check 2: what to verify second"
    ],
    "checklist": [
        {{
            "phase": "Detection",
            "steps": [
                {{
                    "step": 1,
                    "action": "what to do",
                    "command": "actual command if applicable",
                    "expected_output": "what success looks like",
                    "time_estimate": "2 minutes"
                }}
            ]
        }},
        {{
            "phase": "Containment",
            "steps": [
                {{
                    "step": 1,
                    "action": "what to do",
                    "command": "actual command if applicable",
                    "expected_output": "what success looks like",
                    "time_estimate": "5 minutes"
                }}
            ]
        }},
        {{
            "phase": "Resolution",
            "steps": [
                {{
                    "step": 1,
                    "action": "what to do",
                    "command": "actual command if applicable",
                    "expected_output": "what success looks like",
                    "time_estimate": "10 minutes"
                }}
            ]
        }},
        {{
            "phase": "Post-Incident",
            "steps": [
                {{
                    "step": 1,
                    "action": "what to do",
                    "command": "actual command if applicable",
                    "expected_output": "what success looks like",
                    "time_estimate": "15 minutes"
                }}
            ]
        }}
    ],
    "escalation_path": [
        "Level 1: On-call engineer",
        "Level 2: Team lead",
        "Level 3: CTO"
    ],
    "key_metrics_to_monitor": [
        "metric 1",
        "metric 2"
    ],
    "prevention_measures": [
        "measure 1",
        "measure 2"
    ],
    "lessons_learned": "key takeaways from this incident"
}}
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
            "title": "Incident Response Cookbook",
            "checklist": [],
            "lessons_learned": response_text
        }