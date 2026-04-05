"""ArXiv retrieval tool for academic paper search.

Wraps the arxiv Python library as a LangChain @tool for use
by the Retriever agent inside the research pipeline.
"""

import json
import logging
from typing import Optional

import arxiv
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def search_arxiv(query: str, max_results: Optional[int] = 5) -> str:
    """Search ArXiv for academic research papers matching a query.

    Uses the official ArXiv API to retrieve paper metadata including
    titles, authors, abstracts, publication dates, and PDF links.
    Best for academic, scientific, and technical research questions.

    Args:
        query: Natural language or keyword search string
            (e.g. "large language model reasoning chain-of-thought").
        max_results: Maximum number of papers to return (default 5).

    Returns:
        str: JSON string containing a list of paper dicts, each with:
            source, title, authors, abstract, url, published, categories.
    """
    logger.info("Searching ArXiv: query=%s, max_results=%d", query, max_results or 5)

    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results or 5,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    results = []
    try:
        for paper in client.results(search):
            results.append(
                {
                    "source": "arxiv",
                    "title": paper.title,
                    "authors": [a.name for a in paper.authors],
                    "abstract": paper.summary[:800],
                    "url": paper.entry_id,
                    "pdf_url": paper.pdf_url,
                    "published": paper.published.isoformat() if paper.published else "",
                    "categories": paper.categories,
                }
            )
    except Exception as exc:
        logger.error("ArXiv search failed: %s", exc)
        return json.dumps({"error": str(exc), "results": []})

    logger.info("ArXiv search complete: found %d papers", len(results))
    return json.dumps({"source": "arxiv", "query": query, "results": results}, indent=2)
