def micro_summarize_prompt(title: str, content: str, source: str, metadata: dict) -> str:
    return f"""Summarize this {source} result for a product competitive analysis. Be factual and concise.

Title: {title}
Content: {content[:600]}
Metadata: {metadata}

Return a 1–2 sentence summary (max 150 tokens) covering:
- What it does (core function)
- Who it targets (if clear)
- One notable signal (stars, traction, activity, sentiment)

No preamble. Just the summary."""
