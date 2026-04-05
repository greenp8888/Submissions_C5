"""
tools/web_search.py — Tavily Web Search Tool

USE THIS TOOL FOR:
- Real-time information (news, sports scores, stock prices, current events)
- Pop culture, celebrities, entertainment
- Recent product launches, company news
- Anything that changes day-to-day

DO NOT USE FOR:
- Academic research (use arxiv_search)
- Content from uploaded user documents (use chroma_local_search)

Analogy: This is your team's internet-connected researcher who can
Google anything that happened in the last 24 hours.
"""

import os
from typing import List, Dict
from langchain_core.tools import tool
from tavily import TavilyClient


@tool
def tavily_web_search(query: str, api_key: str = "") -> List[Dict[str, str]]:
    """
    Search the live web using Tavily Search API.
    
    Best for: Current events, sports stats, news, celebrity info, 
    product launches, real-time data, pop culture.
    NOT for: Academic papers, scientific theories, or uploaded documents.
    
    Args:
        query: A focused, specific search query (under 200 chars works best)
        api_key: The user's Tavily API key from the frontend
    
    Returns:
        List of dicts with 'source' (URL) and 'content' (extracted text snippet)
    """
    # Use explicitly passed key first to avoid race conditions in multi-user environments
    resolved_api_key = api_key or os.environ.get("TAVILY_API_KEY")
    if not resolved_api_key:
        return [{"source": "error", "content": "TAVILY_API_KEY not set. Add it in the sidebar."}]

    try:
        client = TavilyClient(api_key=resolved_api_key)
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True,
        )

        results = []

        # Tavily's own AI-synthesized answer — often the highest quality snippet
        if response.get("answer"):
            results.append({
                "source": "Tavily AI Answer (Web Synthesis)",
                "content": response["answer"],
            })

        for result in response.get("results", []):
            results.append({
                "source": result.get("url", "Unknown URL"),
                "content": result.get("content", "No content extracted."),
            })

        return results if results else [{"source": "Tavily", "content": "No results found for this query."}]

    except Exception as e:
        return [{"source": "error", "content": f"Tavily search failed: {str(e)}"}]