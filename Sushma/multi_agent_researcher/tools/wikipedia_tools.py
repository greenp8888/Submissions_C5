"""Wikipedia retrieval tool for encyclopedic background knowledge.

Wraps the wikipedia Python library as a LangChain @tool for use
by the Retriever agent inside the research pipeline.
"""

import json
import logging
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def wikipedia_search(query: str, sentences: Optional[int] = 8) -> str:
    """Search Wikipedia for encyclopedic background information.

    Retrieves article summaries from Wikipedia. Best for foundational
    concepts, historical background, definitions, and general knowledge
    that does not require up-to-date information.

    Args:
        query: The topic or concept to look up on Wikipedia.
        sentences: Number of summary sentences to return (default 8).

    Returns:
        str: JSON string containing a list of result dicts, each with:
            source, title, summary, url.
    """
    import wikipedia as wiki_lib

    logger.info("Wikipedia search: query=%s", query)

    results = []
    try:
        wiki_lib.set_lang("en")
        search_results = wiki_lib.search(query, results=3)

        for title in search_results[:3]:
            try:
                page = wiki_lib.page(title, auto_suggest=False)
                summary = wiki_lib.summary(title, sentences=sentences or 8, auto_suggest=False)
                results.append(
                    {
                        "source": "wikipedia",
                        "title": page.title,
                        "summary": summary,
                        "url": page.url,
                        "categories": page.categories[:5],
                    }
                )
            except wiki_lib.exceptions.DisambiguationError as e:
                try:
                    page = wiki_lib.page(e.options[0], auto_suggest=False)
                    summary = wiki_lib.summary(e.options[0], sentences=sentences or 8, auto_suggest=False)
                    results.append(
                        {
                            "source": "wikipedia",
                            "title": page.title,
                            "summary": summary,
                            "url": page.url,
                            "categories": page.categories[:5],
                        }
                    )
                except Exception:
                    continue
            except Exception as page_exc:
                logger.warning("Wikipedia page error for '%s': %s", title, page_exc)
                continue

    except Exception as exc:
        logger.error("Wikipedia search failed: %s", exc)
        return json.dumps({"error": str(exc), "results": []})

    logger.info("Wikipedia search complete: found %d articles", len(results))
    return json.dumps(
        {"source": "wikipedia", "query": query, "results": results}, indent=2
    )
