import anthropic
import json
from utils.helpers import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def generate_remediation(classified_logs: dict) -> dict:
    issues_text = json.dumps(classified_logs.get("issues", []), indent=2)

    prompt = f"""You are an expert DevOps Site Reliability Engineer (SRE).

Analyze these issues and provide remediation steps.

ISSUES FOUND:
{issues_text}

AFFECTED SERVICES: {', '.join(classified_logs.get('affected_services', []))}

Return ONLY a valid JSON object. No markdown. No code blocks. No explanation before or after.
Do NOT wrap the response in ```json or ``` tags.

The JSON must have exactly this structure:

{{
    "overall_recommendation": "Write one or two plain sentences summarizing what the team should do first. No JSON here, just plain text.",
    "priority_order": ["ISSUE-1", "ISSUE-2", "ISSUE-3"],
    "remediations": [
        {{
            "issue_id": "ISSUE-1",
            "severity": "CRITICAL",
            "title": "Short plain text title of the issue",
            "root_cause": "Write one or two plain sentences explaining why this happened. No JSON here.",
            "immediate_action": "Write one plain sentence describing what to do right now. No JSON here.",
            "steps": [
                "Step 1: Do this specific thing first",
                "Step 2: Then do this next thing",
                "Step 3: Verify the fix worked"
            ],
            "commands": [
                "kubectl rollout restart deployment/payment-service -n production",
                "kubectl get pods -n production -w"
            ],
            "prevention": "Write one or two plain sentences on how to prevent this in future. No JSON here.",
            "estimated_time": "10 minutes"
        }}
    ]
}}

CRITICAL RULES:
- Return ONLY the JSON. Nothing before it. Nothing after it.
- Every string value must be plain human readable text.
- The steps array must contain plain strings like "Step 1: do this". NOT nested objects.
- The commands array must contain plain bash command strings only.
- overall_recommendation must be a plain string sentence.
- root_cause must be a plain string sentence.
- immediate_action must be a plain string sentence.
- prevention must be a plain string sentence.
- Do NOT nest JSON objects inside string fields.
- Do NOT use markdown inside any field value.
- Create one remediation entry per issue found.

ISSUES TO REMEDIATE:
{issues_text}
"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text.strip()

    # Strip markdown code blocks if Claude adds them anyway
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        response_text = "\n".join(lines).strip()

    try:
        start = response_text.find('{')
        end   = response_text.rfind('}') + 1
        json_str = response_text[start:end]
        parsed = json.loads(json_str)

        # Safety: flatten any field that ended up as dict/list when it should be a string
        for key in ["overall_recommendation"]:
            val = parsed.get(key, "")
            if isinstance(val, (dict, list)):
                parsed[key] = json.dumps(val)

        # Safety: fix each remediation entry
        for rem in parsed.get("remediations", []):
            if not isinstance(rem, dict):
                continue
            for field in ["root_cause", "immediate_action", "prevention", "title", "estimated_time"]:
                val = rem.get(field, "")
                if isinstance(val, (dict, list)):
                    rem[field] = json.dumps(val)

            # Steps must be list of strings
            steps = rem.get("steps", [])
            if isinstance(steps, str):
                try:
                    steps = json.loads(steps)
                except Exception:
                    steps = [steps]
            clean_steps = []
            for s in steps:
                if isinstance(s, str):
                    clean_steps.append(s)
                elif isinstance(s, dict):
                    # flatten dict step to readable string
                    action = s.get("action") or s.get("step") or str(s)
                    clean_steps.append(str(action))
                else:
                    clean_steps.append(str(s))
            rem["steps"] = clean_steps

            # Commands must be list of strings
            commands = rem.get("commands", [])
            if isinstance(commands, str):
                try:
                    commands = json.loads(commands)
                except Exception:
                    commands = [commands]
            rem["commands"] = [str(c) for c in commands if c]

        return parsed

    except Exception as e:
        return {
            "overall_recommendation": f"Manual review required. Parser error: {str(e)}",
            "priority_order": [],
            "remediations": []
        }
