import anthropic
from utils.helpers import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def classify_logs(log_content: str) -> dict:
    prompt = f"""You are an expert DevOps log analyzer.
    
Analyze the following logs and extract:
1. List of issues found (with severity: CRITICAL, HIGH, MEDIUM, LOW)
2. Affected services
3. Error patterns
4. Timestamps of key events
5. Summary of what went wrong

Return your response in this exact JSON format:
{{
    "summary": "brief summary of what happened",
    "issues": [
        {{
            "id": "ISSUE-1",
            "severity": "CRITICAL",
            "title": "issue title",
            "description": "detailed description",
            "affected_service": "service name",
            "timestamp": "timestamp if available",
            "error_pattern": "the actual error pattern found"
        }}
    ],
    "affected_services": ["service1", "service2"],
    "total_errors": 0,
    "time_range": "start - end time if available"
}}

LOGS TO ANALYZE:
{log_content}
"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    import json
    response_text = message.content[0].text
    
    try:
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        json_str = response_text[start:end]
        return json.loads(json_str)
    except:
        return {
            "summary": response_text,
            "issues": [],
            "affected_services": [],
            "total_errors": 0,
            "time_range": "unknown"
        }