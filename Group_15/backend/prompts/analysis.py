def analysis_prompt(idea: str, audience: str, items_json: str) -> str:
    return f"""You are a product strategist. Analyze these research results for a product idea and return structured insights.

Product idea: {idea}
Target audience: {audience or "not specified"}

Research results (compressed):
{items_json}

Return ONLY valid JSON with this exact structure — no markdown, no explanation:
{{
  "gap_analysis": ["gap or unmet need 1", "gap 2", "gap 3"],
  "suggested_features": [
    {{"feature": "feature name", "rationale": "why this matters", "priority": "high|medium|low", "source_urls": ["url1", "url2"]}},
    ...
  ],
  "competitive_landscape": "2–3 sentences describing the competitive situation",
  "sentiment": {{
    "overall": "positive|neutral|negative",
    "by_source": {{
      "github": "positive|neutral|negative|insufficient_data",
      "reddit": "...",
      "hn": "...",
      "ph": "...",
      "ai4that": "...",
      "yc": "..."
    }}
  }},
  "market_signals": ["key signal 1", "key signal 2", "key signal 3"]
}}

Be direct. Base every point on the research results provided. Do not invent signals. For source_urls, include 1–3 URLs from the research results that directly support each suggested feature."""
