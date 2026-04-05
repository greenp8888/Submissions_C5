import json
from graph.state import GraphState
from prompts.analysis import analysis_prompt
from utils.llm import call_llm


def analysis(state: GraphState) -> dict:
    print("\n" + "="*80)
    print("🔵 ANALYSIS - Generating insights with GPT-4.1")
    print("="*80)

    matched_items = state.get("matched_items", [])
    idea = state["idea_description"]
    audience = state.get("audience", "")

    print(f"📥 Analyzing {len(matched_items)} items...")

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
        print(f"⚠️  Truncating items JSON from {len(items_json)} to 2000 chars")
        items_json = items_json[:2000]

    prompt = analysis_prompt(idea, audience, items_json)

    try:
        print("📡 Calling GPT-4.1 for competitive analysis...")
        content = call_llm(prompt, max_tokens=2048)
        analysis_result = json.loads(content)

        print("✅ Analysis generated successfully:")
        print(f"  • Gap analysis: {len(analysis_result.get('gap_analysis', []))} points")
        print(f"  • Suggested features: {len(analysis_result.get('suggested_features', []))}")
        print(f"  • Market signals: {len(analysis_result.get('market_signals', []))}")
        print(f"  • Overall sentiment: {analysis_result.get('sentiment', {}).get('overall', 'N/A')}")
        print()

        return {"analysis": analysis_result}

    except (json.JSONDecodeError, Exception) as e:
        print(f"❌ Analysis failed: {e}")
        print("🔄 Returning fallback analysis\n")

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
