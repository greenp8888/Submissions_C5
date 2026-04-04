import json
import os
from anthropic import Anthropic
from graph.state import GraphState
from prompts.analysis import analysis_prompt


def analysis(state: GraphState) -> dict:
    matched_items = state.get("matched_items", [])
    idea = state["idea_description"]
    audience = state.get("audience", "")

    items_compressed = []
    for item in matched_items[:20]:
        items_compressed.append({
            "source": item["source"],
            "title": item["title"],
            "summary": item["summary"][:100],
            "score": round(item["relevance_score"], 2),
            "meta": {k: v for k, v in item["metadata"].items() if k in ["stars", "votes", "points", "score"]}
        })

    items_json = json.dumps(items_compressed, indent=2)

    if len(items_json) > 2000:
        items_json = items_json[:2000]

    prompt = analysis_prompt(idea, audience, items_json)

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text
        analysis_result = json.loads(content)

        return {"analysis": analysis_result}

    except (json.JSONDecodeError, Exception) as e:
        return {
            "analysis": {
                "gap_analysis": ["Unable to generate analysis"],
                "suggested_features": [],
                "competitive_landscape": "Analysis unavailable",
                "sentiment": {
                    "overall": "neutral",
                    "by_source": {}
                },
                "market_signals": []
            }
        }
