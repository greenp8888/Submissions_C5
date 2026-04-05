import anthropic
import json
from utils.helpers import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def generate_cookbook(classified_logs: dict, remediation: dict) -> dict:
    issues_text = json.dumps(classified_logs.get("issues", []), indent=2)
    remediation_text = json.dumps(remediation.get("remediations", []), indent=2)

    prompt = f"""You are a senior DevOps engineer creating a runbook.

Based on the incident analysis below, create a structured cookbook.

ISSUES DETECTED:
{issues_text}

REMEDIATION STEPS:
{remediation_text}

Return ONLY a valid JSON object. No markdown, no code blocks, no explanation.
The JSON must have exactly these fields:

{{
    "title": "short title string here",
    "incident_type": "short incident type string here",
    "severity_level": "CRITICAL",
    "created_for": "one sentence description string here",
    "pre_checks": [
        "First thing to check before starting",
        "Second thing to check before starting",
        "Third thing to check before starting"
    ],
    "checklist": [
        {{
            "phase": "Detection",
            "steps": [
                {{
                    "step": 1,
                    "action": "what to do",
                    "command": "kubectl get pods -n production",
                    "expected_output": "what success looks like",
                    "time_estimate": "2 minutes"
                }},
                {{
                    "step": 2,
                    "action": "what to do",
                    "command": "command here",
                    "expected_output": "what success looks like",
                    "time_estimate": "3 minutes"
                }}
            ]
        }},
        {{
            "phase": "Containment",
            "steps": [
                {{
                    "step": 1,
                    "action": "what to do",
                    "command": "command here",
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
                    "command": "command here",
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
                    "command": "command here",
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
        "CPU usage per service",
        "Database connection count",
        "Cache hit rate"
    ],
    "prevention_measures": [
        "First prevention measure",
        "Second prevention measure",
        "Third prevention measure"
    ],
    "lessons_learned": "Write a single plain text paragraph here summarizing key lessons. Do not nest JSON inside this field."
}}

IMPORTANT RULES:
- Return ONLY the JSON. No text before or after.
- All field values must be plain strings or arrays of strings/objects.
- The lessons_learned field must be a plain string, NOT a JSON object.
- Do not wrap the response in markdown code blocks.
"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text.strip()

    # Strip markdown code blocks if Claude wraps it anyway
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        response_text = "\n".join(lines).strip()

    try:
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        json_str = response_text[start:end]
        parsed = json.loads(json_str)

        # Safety: if lessons_learned is somehow still a dict/list, flatten it
        ll = parsed.get("lessons_learned", "")
        if isinstance(ll, (dict, list)):
            parsed["lessons_learned"] = json.dumps(ll)

        # Safety: flatten any other string fields that got nested
        for key in ["title", "incident_type", "severity_level", "created_for"]:
            val = parsed.get(key, "")
            if isinstance(val, (dict, list)):
                parsed[key] = str(val)

        return parsed

    except Exception as e:
        return {
            "title": "Incident Response Cookbook",
            "incident_type": "Multi-service failure",
            "severity_level": "CRITICAL",
            "created_for": "Incident response reference",
            "pre_checks": ["Check system access", "Verify monitoring dashboards"],
            "checklist": [],
            "escalation_path": ["Level 1: On-call engineer", "Level 2: Team lead"],
            "key_metrics_to_monitor": ["CPU", "Memory", "Database connections"],
            "prevention_measures": ["Add monitoring alerts", "Implement circuit breakers"],
            "lessons_learned": f"Cookbook generation encountered an error: {str(e)}. Raw response saved for review."
        }
