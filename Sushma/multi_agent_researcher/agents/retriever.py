"""Retriever Agent — multi-source document retrieval node.

Executes retrieval across all selected sources for each sub-query.
Uses LangChain tools directly and accumulates results into the
retrieved_documents list. Supports retry via conditional edge.
"""

import json
import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from multi_agent_researcher.models.state import ResearchState
from multi_agent_researcher.tools.arxiv_tools import search_arxiv
from multi_agent_researcher.tools.pdf_tools import load_pdf_document
from multi_agent_researcher.tools.serpapi_tools import google_search
from multi_agent_researcher.tools.tavily_tools import tavily_web_search
from multi_agent_researcher.tools.wikipedia_tools import wikipedia_search

logger = logging.getLogger(__name__)

# Maps source name → tool function
SOURCE_TOOL_MAP = {
    "arxiv": search_arxiv,
    "tavily": tavily_web_search,
    "wikipedia": wikipedia_search,
    "serpapi": google_search,
    "pdf": load_pdf_document,
}

RETRIEVER_SYSTEM_PROMPT = """You are the Retriever Agent in a multi-agent research system.

You have already retrieved documents from multiple sources. Your job is to
review the retrieved content and confirm it is sufficient for the research question.

Respond with a brief assessment (2-3 sentences) noting:
- How many relevant documents were found
- Whether the coverage is sufficient for the research question
- Any notable gaps
"""


def _invoke_tool(tool_fn, **kwargs) -> list[dict]:
    """Invoke a retrieval tool and parse its JSON output into a list of dicts.

    Args:
        tool_fn: The LangChain @tool function to call.
        **kwargs: Arguments to pass to the tool.

    Returns:
        list[dict]: Parsed result list, or empty list on failure.
    """
    try:
        raw = tool_fn.invoke(kwargs)
        if isinstance(raw, str):
            parsed = json.loads(raw)
        else:
            parsed = raw

        if "error" in parsed and not parsed.get("results"):
            logger.warning("Tool returned error: %s", parsed.get("error"))
            return []

        return parsed.get("results", [])
    except Exception as exc:
        logger.error("Tool invocation failed for %s: %s", tool_fn.name, exc)
        return []


def retriever_node(state: ResearchState, llm: ChatOpenAI) -> dict:
    """Retriever node — fetches documents from all selected sources.

    For each sub-query, invokes the appropriate retrieval tool for each
    selected source. All results are accumulated into retrieved_documents.
    Increments retrieval_attempts for the conditional retry edge.

    Args:
        state: The current ResearchState.
        llm: The configured ChatOpenAI (OpenRouter) model.

    Returns:
        dict: State updates with retrieved_documents appended,
              retrieval_attempts incremented, and status updated.
    """
    sub_queries = state.get("sub_queries", [state["query"]])
    sources = state.get("sources_to_use", ["tavily", "wikipedia"])
    pdf_paths = state.get("pdf_paths", [])
    attempt = state.get("retrieval_attempts", 0) + 1

    logger.info(
        "Retriever: attempt=%d, sub_queries=%d, sources=%s",
        attempt,
        len(sub_queries),
        sources,
    )
    print(f"\n{'='*60}")
    print(f"  AGENT: Retriever (attempt {attempt})")
    print(f"{'='*60}")

    all_docs: list[dict] = []

    for sub_query in sub_queries:
        print(f"  Retrieving for: {sub_query[:70]}...")

        for source in sources:
            if source == "pdf":
                # PDF tool takes file paths, not queries
                for path in pdf_paths:
                    print(f"    [{source}] Loading: {path}")
                    docs = _invoke_tool(load_pdf_document, file_path=path)
                    for doc in docs:
                        doc["sub_query"] = sub_query
                    all_docs.extend(docs)
                continue

            tool_fn = SOURCE_TOOL_MAP.get(source)
            if tool_fn is None:
                logger.warning("Unknown source: %s", source)
                continue

            print(f"    [{source}] querying...")

            if source in ("arxiv", "tavily", "wikipedia"):
                docs = _invoke_tool(tool_fn, query=sub_query)
            elif source == "serpapi":
                docs = _invoke_tool(tool_fn, query=sub_query)
            else:
                docs = _invoke_tool(tool_fn, query=sub_query)

            for doc in docs:
                doc["sub_query"] = sub_query

            all_docs.extend(docs)
            logger.info(
                "  Source '%s' returned %d docs for '%s'",
                source,
                len(docs),
                sub_query[:50],
            )

    print(f"  Total documents retrieved this round: {len(all_docs)}")

    # Brief LLM assessment for observability
    assessment_msg = f"Retrieved {len(all_docs)} documents across {len(sources)} sources for {len(sub_queries)} sub-queries."
    llm_messages = [
        SystemMessage(content=RETRIEVER_SYSTEM_PROMPT),
        HumanMessage(content=assessment_msg),
    ]
    try:
        assessment = llm.invoke(llm_messages)
        assessment_text = assessment.content
    except Exception:
        assessment_text = assessment_msg

    return {
        "retrieved_documents": all_docs,
        "retrieval_attempts": attempt,
        "status": f"retrieved (attempt {attempt}, docs={len(all_docs)})",
        "messages": [
            HumanMessage(content=assessment_msg),
            AIMessage(content=assessment_text),
        ],
    }
