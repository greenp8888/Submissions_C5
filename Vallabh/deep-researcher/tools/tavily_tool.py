"""
Tavily Web Search Tool
Searches the web for news articles, reports, and recent information.
Tavily provides high-quality search results optimized for AI/LLM use.
"""
from __future__ import annotations

import logging
from typing import Optional

from langchain_core.tools import tool

from config import settings

logger = logging.getLogger(__name__)


@tool
def search_web(query: str, max_results: int = 5, search_depth: str = "advanced") -> list[dict]:
    """
    Search the web using Tavily for news, articles, and reports.

    Args:
        query: Search query
        max_results: Maximum results to return
        search_depth: "basic" for quick search, "advanced" for deeper search

    Returns:
        List of dicts with title, content, url, score
    """
    if not settings.TAVILY_API_KEY:
        logger.warning("Tavily API key not configured — returning empty results")
        return [{"error": "TAVILY_API_KEY not set. Get one at https://tavily.com"}]

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_raw_content=False,
        )

        results = []
        for item in response.get("results", []):
            results.append({
                "title": item.get("title", "Untitled"),
                "content": item.get("content", "")[:3000],
                "url": item.get("url", ""),
                "score": item.get("score", 0.0),
                "published_date": item.get("published_date"),
                "source_type": "WEB",
            })

        logger.info(f"Tavily: Found {len(results)} results for '{query}'")
        return results

    except ImportError:
        logger.warning("tavily-python package not installed")
        return [{"error": "tavily-python not installed. Run: pip install tavily-python"}]
    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        return [{"error": str(e)}]


@tool
def search_news(query: str, max_results: int = 5) -> list[dict]:
    """
    Search specifically for recent news articles.

    Args:
        query: News search query
        max_results: Maximum results

    Returns:
        List of news article dicts
    """
    if not settings.TAVILY_API_KEY:
        return [{"error": "TAVILY_API_KEY not set"}]

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            topic="news",
        )

        results = []
        for item in response.get("results", []):
            results.append({
                "title": item.get("title", "Untitled"),
                "content": item.get("content", "")[:3000],
                "url": item.get("url", ""),
                "score": item.get("score", 0.0),
                "published_date": item.get("published_date"),
                "source_type": "NEWS",
            })

        logger.info(f"Tavily News: Found {len(results)} articles for '{query}'")
        return results

    except Exception as e:
        logger.error(f"News search failed: {e}")
        return [{"error": str(e)}]


tavily_tools = [search_web, search_news]
