"""
=============================================================================
Contextual Retriever Agent
=============================================================================
Pulls data from multiple sources (ArXiv, Wikipedia, Tavily Web Search)
based on the query plan's sub-questions. Deduplicates and scores results.

Key Patterns:
- Parallel retrieval across source types
- URL-based deduplication
- Relevance scoring from search APIs
- Source ID generation for citation tracking
=============================================================================
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any

from state import ResearchState, Source, SourceType
from tools.arxiv_tool import search_arxiv
from tools.wikipedia_tool import search_wikipedia
from tools.tavily_tool import search_web, search_news
from config import settings

logger = logging.getLogger(__name__)


def _generate_source_id(source_type: str, index: int) -> str:
    """Generate a deterministic source ID."""
    return f"{source_type.lower()}-{index + 1:03d}"


def _dedup_sources(sources: list[dict]) -> list[dict]:
    """Deduplicate sources by URL and title similarity."""
    seen_urls = set()
    seen_titles = set()
    unique = []

    for s in sources:
        url = s.get("url", "")
        title = s.get("title", "").lower().strip()

        if url and url in seen_urls:
            continue
        if title and title in seen_titles:
            continue

        if url:
            seen_urls.add(url)
        if title:
            seen_titles.add(title)
        unique.append(s)

    return unique


def retrieve_sources(state: ResearchState) -> dict:
    """
    Contextual Retriever Agent node for LangGraph.

    For each sub-question in the query plan, searches across
    ArXiv, Wikipedia, and Tavily (web + news).

    Reads: sub_questions, retrieval_round, depth
    Writes: sources, retrieval_summary, retrieval_round, current_agent
    """
    logger.info("🔍 Contextual Retriever Agent starting...")

    sub_questions = state.get("sub_questions", [])
    current_round = state.get("retrieval_round", 0)
    depth = state.get("depth", "standard")

    if not sub_questions:
        return {
            "sources": [],
            "retrieval_summary": "No sub-questions to research.",
            "retrieval_round": current_round,
            "current_agent": "retriever",
            "error_trace": ["Retriever: No sub-questions provided"],
        }

    # Adjust max results based on depth
    max_per_source = {"quick": 2, "standard": 3, "deep": 5}.get(depth, 3)
    all_sources = []
    source_counter = {"ARXIV": 0, "WIKIPEDIA": 0, "WEB": 0, "NEWS": 0}

    for sq in sub_questions:
        question = sq.get("question", "")
        keywords = sq.get("search_keywords", [])
        sq_id = sq.get("id", 0)
        search_query = " ".join(keywords[:4]) if keywords else question

        logger.info(f"  📖 Sub-Q {sq_id}: {question[:60]}...")

        # ── ArXiv (academic papers) ──
        try:
            arxiv_results = search_arxiv.invoke({
                "query": search_query,
                "max_results": max_per_source,
            })
            for r in arxiv_results:
                if "error" in r:
                    continue
                idx = source_counter["ARXIV"]
                source_counter["ARXIV"] += 1
                all_sources.append({
                    "id": _generate_source_id("arxiv", idx),
                    "title": r.get("title", "Untitled"),
                    "source_type": "ARXIV",
                    "url": r.get("url"),
                    "authors": r.get("authors"),
                    "published_date": r.get("published"),
                    "content": r.get("summary", "")[:3000],
                    "relevance_score": 0.8,  # ArXiv results are generally relevant
                    "sub_question_ids": [sq_id],
                })
        except Exception as e:
            logger.warning(f"  ArXiv failed for sub-Q {sq_id}: {e}")

        # ── Wikipedia (background) ──
        try:
            wiki_results = search_wikipedia.invoke({
                "query": question,
                "max_results": min(max_per_source, 2),  # Fewer wiki articles
            })
            for r in wiki_results:
                if "error" in r:
                    continue
                idx = source_counter["WIKIPEDIA"]
                source_counter["WIKIPEDIA"] += 1
                content = r.get("content", r.get("summary", ""))
                all_sources.append({
                    "id": _generate_source_id("wiki", idx),
                    "title": r.get("title", "Untitled"),
                    "source_type": "WIKIPEDIA",
                    "url": r.get("url"),
                    "authors": "Wikipedia Contributors",
                    "published_date": None,
                    "content": content[:3000],
                    "relevance_score": 0.6,
                    "sub_question_ids": [sq_id],
                })
        except Exception as e:
            logger.warning(f"  Wikipedia failed for sub-Q {sq_id}: {e}")

        # ── Tavily Web Search ──
        try:
            web_results = search_web.invoke({
                "query": search_query,
                "max_results": max_per_source,
            })
            for r in web_results:
                if "error" in r:
                    continue
                idx = source_counter["WEB"]
                source_counter["WEB"] += 1
                all_sources.append({
                    "id": _generate_source_id("web", idx),
                    "title": r.get("title", "Untitled"),
                    "source_type": "WEB",
                    "url": r.get("url"),
                    "authors": None,
                    "published_date": r.get("published_date"),
                    "content": r.get("content", "")[:3000],
                    "relevance_score": r.get("score", 0.5),
                    "sub_question_ids": [sq_id],
                })
        except Exception as e:
            logger.warning(f"  Web search failed for sub-Q {sq_id}: {e}")

        # ── Tavily News (for current events) ──
        if sq.get("priority", 5) <= 2:  # Only for high-priority questions
            try:
                news_results = search_news.invoke({
                    "query": search_query,
                    "max_results": min(max_per_source, 3),
                })
                for r in news_results:
                    if "error" in r:
                        continue
                    idx = source_counter["NEWS"]
                    source_counter["NEWS"] += 1
                    all_sources.append({
                        "id": _generate_source_id("news", idx),
                        "title": r.get("title", "Untitled"),
                        "source_type": "NEWS",
                        "url": r.get("url"),
                        "authors": None,
                        "published_date": r.get("published_date"),
                        "content": r.get("content", "")[:3000],
                        "relevance_score": r.get("score", 0.5),
                        "sub_question_ids": [sq_id],
                    })
            except Exception as e:
                logger.warning(f"  News search failed for sub-Q {sq_id}: {e}")

    # Deduplicate
    unique_sources = _dedup_sources(all_sources)

    summary = (
        f"Retrieved {len(unique_sources)} unique sources "
        f"(ArXiv: {source_counter['ARXIV']}, Wikipedia: {source_counter['WIKIPEDIA']}, "
        f"Web: {source_counter['WEB']}, News: {source_counter['NEWS']}) "
        f"across {len(sub_questions)} sub-questions. Round {current_round + 1}."
    )

    logger.info(f"✅ Retrieval complete: {len(unique_sources)} unique sources")

    return {
        "sources": unique_sources,
        "retrieval_summary": summary,
        "retrieval_round": current_round + 1,
        "current_agent": "retriever",
    }
