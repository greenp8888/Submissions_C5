"""Critical Analysis Agent — synthesizes and validates retrieved documents.

Receives all retrieved documents and the original query, then produces:
- A synthesized summary of key findings
- A list of contradictions between sources
- A list of validated (credible) source URLs
"""

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from multi_agent_researcher.models.state import ResearchState

logger = logging.getLogger(__name__)

ANALYZER_SYSTEM_PROMPT = """You are the Critical Analysis Agent in a multi-agent research system.

You receive a research question and a collection of retrieved documents from multiple sources.
Your task is to critically analyze the evidence and produce structured findings.

## Your Analysis Must Cover

1. **Summary**: Synthesize the key findings across all sources (300-500 words).
   Focus on what the evidence collectively says about the research question.

2. **Contradictions**: Identify specific conflicting claims between sources.
   Be concrete — name what contradicts what.

3. **Source Validation**: Rate each source's credibility.
   - arxiv papers = high credibility (peer-reviewed or preprint)
   - Wikipedia = medium credibility (encyclopedic, may be outdated)
   - tavily/serpapi/web = variable (check for reputable outlets)

## Output Format (MUST be valid JSON)
{
  "analysis_summary": "your synthesized summary here...",
  "contradictions": [
    "Source A claims X, but Source B claims Y",
    "The arxiv paper states Z, contradicting the news article"
  ],
  "validated_sources": ["https://url1", "https://url2"],
  "key_themes": ["theme1", "theme2", "theme3"],
  "evidence_quality": "strong | moderate | weak",
  "gaps_identified": ["missing information 1", "missing information 2"]
}

Output ONLY valid JSON. No markdown, no text outside the JSON.
"""


def _format_documents_for_prompt(docs: list[dict], max_docs: int = 15) -> str:
    """Format retrieved documents into a readable prompt section.

    Args:
        docs: List of retrieved document dicts.
        max_docs: Maximum number of documents to include.

    Returns:
        str: Formatted document block for the LLM prompt.
    """
    if not docs:
        return "No documents retrieved."

    lines = []
    for i, doc in enumerate(docs[:max_docs]):
        source = doc.get("source", "unknown")
        title = doc.get("title", doc.get("file_name", "Untitled"))
        url = doc.get("url", doc.get("pdf_url", "no-url"))
        content = (
            doc.get("content")
            or doc.get("abstract")
            or doc.get("summary")
            or doc.get("snippet")
            or ""
        )
        lines.append(
            f"[{i+1}] SOURCE={source} | TITLE={title}\n"
            f"    URL={url}\n"
            f"    CONTENT={content[:500]}\n"
        )

    if len(docs) > max_docs:
        lines.append(f"\n... and {len(docs) - max_docs} more documents not shown.")

    return "\n".join(lines)


def analyzer_node(state: ResearchState, llm: ChatOpenAI) -> dict:
    """Analyzer node — critically analyzes all retrieved documents.

    Args:
        state: The current ResearchState with retrieved_documents populated.
        llm: The configured ChatOpenAI (OpenRouter) model.

    Returns:
        dict: State updates with analysis_summary, contradictions,
              validated_sources, and status.
    """
    query = state["query"]
    docs = state.get("retrieved_documents", [])

    logger.info("Analyzer: processing %d documents for query='%s'", len(docs), query[:60])
    print(f"\n{'='*60}")
    print(f"  AGENT: Critical Analyzer")
    print(f"{'='*60}")
    print(f"  Analyzing {len(docs)} retrieved documents...")

    doc_block = _format_documents_for_prompt(docs)
    user_content = (
        f"Research Question: {query}\n\n"
        f"Retrieved Documents:\n{doc_block}"
    )

    messages = [
        SystemMessage(content=ANALYZER_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]

    response = None
    try:
        response = llm.invoke(messages)
        raw = response.content.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        analysis = json.loads(raw)
        summary = analysis.get("analysis_summary", "Analysis not available.")
        contradictions = analysis.get("contradictions", [])
        validated_sources = analysis.get("validated_sources", [])
        key_themes = analysis.get("key_themes", [])
        evidence_quality = analysis.get("evidence_quality", "moderate")

    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("Analyzer JSON parse failed (%s) — using fallback", exc)
        try:
            response_content = response.content if response is not None else "Analysis unavailable."
        except Exception:
            response_content = "Analysis unavailable."
        summary = response_content
        contradictions = []
        validated_sources = []
        key_themes = []
        evidence_quality = "unknown"

    logger.info(
        "Analysis complete: contradictions=%d, validated_sources=%d",
        len(contradictions),
        len(validated_sources),
    )
    print(f"  Contradictions found: {len(contradictions)}")
    print(f"  Validated sources: {len(validated_sources)}")
    print(f"  Evidence quality: {evidence_quality}")

    return {
        "analysis_summary": summary,
        "contradictions": contradictions,
        "validated_sources": validated_sources,
        "status": f"analyzed (quality={evidence_quality}, contradictions={len(contradictions)})",
        "messages": [HumanMessage(content=user_content)] + ([response] if response is not None else []),
    }
