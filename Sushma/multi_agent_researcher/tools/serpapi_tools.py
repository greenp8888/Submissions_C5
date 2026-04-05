"""SerpAPI Google Search tool for broad web retrieval.

Wraps the google-search-results (SerpAPI) client as a LangChain
@tool for use by the Retriever agent. Requires SERPAPI_API_KEY.
Falls back gracefully when the key is not configured.
"""

import json
import logging
import os
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def google_search(query: str, num_results: Optional[int] = 5) -> str:
    """Search Google via SerpAPI for broad web results.

    Retrieves organic Google search results including titles, URLs,
    and snippets. Best for broad web coverage, news, company information,
    and sources not indexed by Tavily. Requires SERPAPI_API_KEY.

    Args:
        query: The Google search query string.
        num_results: Number of results to return (default 5).

    Returns:
        str: JSON string containing a list of result dicts, each with:
            source, title, url, snippet, position.
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        logger.warning("SERPAPI_API_KEY not set — google_search skipped")
        return json.dumps(
            {
                "error": "SERPAPI_API_KEY not configured. Set it in .env to enable Google Search.",
                "results": [],
            }
        )

    logger.info("Google search via SerpAPI: query=%s", query)

    try:
        from serpapi import GoogleSearch

        search = GoogleSearch(
            {
                "q": query,
                "num": num_results or 5,
                "api_key": api_key,
            }
        )
        raw = search.get_dict()

        results = []
        for item in raw.get("organic_results", [])[: num_results or 5]:
            results.append(
                {
                    "source": "serpapi",
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "")[:600],
                    "position": item.get("position", 0),
                }
            )

    except Exception as exc:
        logger.error("SerpAPI search failed: %s", exc)
        return json.dumps({"error": str(exc), "results": []})

    logger.info("SerpAPI search complete: found %d results", len(results))
    return json.dumps(
        {"source": "serpapi", "query": query, "results": results}, indent=2
    )
