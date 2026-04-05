"""Tavily web search tool for real-time internet retrieval.

Wraps the Tavily Python client as a LangChain @tool for use
by the Retriever agent inside the research pipeline.
Requires TAVILY_API_KEY to be set in the environment.
"""

import json
import logging
import os
import ssl
import warnings
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def tavily_web_search(query: str, max_results: Optional[int] = 5) -> str:
    """Search the web in real time using Tavily's AI search API.

    Retrieves current news articles, blog posts, reports, and web pages
    relevant to the query. Best for recent events, product information,
    industry news, and any topic needing up-to-date web sources.
    Requires TAVILY_API_KEY environment variable.

    Args:
        query: The search query string.
        max_results: Maximum number of web results to return (default 5).

    Returns:
        str: JSON string containing a list of result dicts, each with:
            source, title, url, content, score.
    """
    from tavily import TavilyClient

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.error("TAVILY_API_KEY not set")
        return json.dumps({"error": "TAVILY_API_KEY not configured", "results": []})

    # Patch ssl for Windows where Python CA bundle lacks required intermediate CAs.
    # The ssl._create_default_https_context patch affects requests (used by TavilyClient).
    ssl._create_default_https_context = ssl._create_unverified_context
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")

    logger.info("Tavily web search: query=%s", query)

    client = TavilyClient(api_key=api_key)

    try:
        response = client.search(
            query=query,
            max_results=max_results or 5,
            include_answer=True,
            include_raw_content=False,
        )

        results = []
        for item in response.get("results", []):
            results.append(
                {
                    "source": "tavily",
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", "")[:800],
                    "score": item.get("score", 0.0),
                }
            )

        answer = response.get("answer", "")

    except Exception as exc:
        logger.error("Tavily search failed: %s", exc)
        return json.dumps({"error": str(exc), "results": []})

    logger.info("Tavily search complete: found %d results", len(results))
    return json.dumps(
        {
            "source": "tavily",
            "query": query,
            "answer": answer,
            "results": results,
        },
        indent=2,
    )
