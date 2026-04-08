def query_builder_prompt(idea: str, audience: str, product_url: str) -> str:
    return f"""You are a product research expert. Given a product idea, generate precise search queries for 6 platforms.

Product idea: {idea}
Target audience: {audience or "not specified"}
Product URL: {product_url or "none"}

Return ONLY a JSON object with these exact keys. No explanation, no markdown, just JSON:
{{
  "github": "search query for finding competing open-source repos",
  "reddit": "search query for finding relevant discussions and pain points",
  "hn": "search query for Hacker News threads",
  "ph": "search query for Product Hunt products",
  "ai4that": "search query for ThereIsAnAIForThat tool search",
  "yc": "search query for YC company search"
}}

Rules:
- Each query should be 3–7 words, highly specific to the product domain
- Reddit query should lean toward problem/pain-point phrasing
- HN query should lean toward technical and founder discussion
- YC query should focus on startup category and market"""
