"""
=============================================================================
Gap Filler Agent
=============================================================================
When the Critical Analysis Agent identifies significant information gaps,
this agent runs additional targeted retrieval to fill them.

Only triggered conditionally (when has_critical_gaps is True and
retrieval_round < MAX_RETRIEVAL_ROUNDS).
=============================================================================
"""
from __future__ import annotations

import logging

from state import ResearchState
from tools.arxiv_tool import search_arxiv
from tools.tavily_tool import search_web
from config import settings

logger = logging.getLogger(__name__)


def fill_gaps(state: ResearchState) -> dict:
    """
    Gap Filler node for LangGraph.

    Uses suggested_queries from information_gaps to do targeted retrieval.

    Reads: information_gaps, retrieval_round
    Writes: sources (appended), retrieval_round, has_critical_gaps, current_agent
    """
    logger.info("🔄 Gap Filler Agent starting...")

    gaps = state.get("information_gaps", [])
    current_round = state.get("retrieval_round", 0)

    if not gaps:
        logger.info("  No gaps to fill.")
        return {
            "sources": [],
            "retrieval_round": current_round,
            "has_critical_gaps": False,
            "current_agent": "gap_filler",
        }

    new_sources = []
    source_idx = len(state.get("sources", []))  # Continue numbering

    for gap in gaps[:5]:  # Limit to top 5 gaps
        queries = gap.get("suggested_queries", [])
        if not queries:
            continue

        description = gap.get("description", "Unknown gap")
        logger.info(f"  🔎 Filling gap: {description[:60]}...")

        for query in queries[:2]:  # 2 queries per gap
            try:
                # Try web search for gaps (often more current)
                results = search_web.invoke({
                    "query": query,
                    "max_results": 3,
                })
                for r in results:
                    if "error" in r:
                        continue
                    new_sources.append({
                        "id": f"gap-{source_idx + 1:03d}",
                        "title": r.get("title", "Untitled"),
                        "source_type": "WEB",
                        "url": r.get("url"),
                        "authors": None,
                        "published_date": r.get("published_date"),
                        "content": r.get("content", "")[:3000],
                        "relevance_score": r.get("score", 0.5),
                        "sub_question_ids": [gap.get("sub_question_id")] if gap.get("sub_question_id") else [],
                    })
                    source_idx += 1
            except Exception as e:
                logger.warning(f"  Gap fill search failed: {e}")

    logger.info(f"✅ Gap filling complete: {len(new_sources)} additional sources found")

    return {
        "sources": new_sources,
        "retrieval_round": current_round + 1,
        "has_critical_gaps": False,  # Don't loop indefinitely
        "current_agent": "gap_filler",
    }
