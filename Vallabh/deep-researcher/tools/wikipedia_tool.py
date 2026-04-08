"""
Wikipedia Search Tool
Searches Wikipedia for background knowledge and context.
"""
from __future__ import annotations

import logging
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def search_wikipedia(query: str, max_results: int = 3) -> list[dict]:
    """
    Search Wikipedia for articles matching the query.

    Args:
        query: Search query
        max_results: Maximum articles to return

    Returns:
        List of dicts with title, summary, url
    """
    try:
        import wikipedia

        wikipedia.set_lang("en")
        search_results = wikipedia.search(query, results=max_results)

        results = []
        for title in search_results:
            try:
                page = wikipedia.page(title, auto_suggest=False)
                results.append({
                    "title": page.title,
                    "summary": page.summary[:2000],
                    "url": page.url,
                    "content": page.content[:4000],
                    "source_type": "WIKIPEDIA",
                })
            except (wikipedia.DisambiguationError, wikipedia.PageError) as e:
                logger.debug(f"Skipping Wikipedia page '{title}': {e}")
                continue

        logger.info(f"Wikipedia: Found {len(results)} articles for '{query}'")
        return results

    except ImportError:
        logger.warning("wikipedia package not installed")
        return [{"error": "wikipedia package not installed. Run: pip install wikipedia"}]
    except Exception as e:
        logger.error(f"Wikipedia search failed: {e}")
        return [{"error": str(e)}]


wikipedia_tools = [search_wikipedia]
