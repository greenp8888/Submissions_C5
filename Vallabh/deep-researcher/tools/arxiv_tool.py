"""
ArXiv Research Paper Search Tool
Searches for academic papers on ArXiv and returns structured results.
"""
from __future__ import annotations

import logging
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def search_arxiv(query: str, max_results: int = 5) -> list[dict]:
    """
    Search ArXiv for research papers matching the query.

    Args:
        query: Search query for academic papers
        max_results: Maximum papers to return (default 5)

    Returns:
        List of dicts with title, summary, authors, url, published
    """
    try:
        import arxiv

        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )

        results = []
        for paper in client.results(search):
            results.append({
                "title": paper.title,
                "summary": paper.summary[:2000],
                "authors": ", ".join(a.name for a in paper.authors[:5]),
                "url": paper.entry_id,
                "published": paper.published.strftime("%Y-%m-%d") if paper.published else None,
                "categories": [c for c in paper.categories],
                "source_type": "ARXIV",
            })

        logger.info(f"ArXiv: Found {len(results)} papers for '{query}'")
        return results

    except ImportError:
        logger.warning("arxiv package not installed")
        return [{"error": "arxiv package not installed. Run: pip install arxiv"}]
    except Exception as e:
        logger.error(f"ArXiv search failed: {e}")
        return [{"error": str(e)}]


arxiv_tools = [search_arxiv]
