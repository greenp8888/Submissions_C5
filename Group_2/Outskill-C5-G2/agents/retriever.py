"""
agents/retriever.py — Dynamic Retriever with Parallel Tool Execution

Reads the routing_plan from the Planner and executes each sub-query
using EXACTLY the tools the Planner prescribed.

Key upgrade over v1:
- No more ReAct agent deciding tools at runtime
- Routing is pre-decided by the Planner (more deterministic, more transparent)
- Parallel execution for sub-queries with multiple tools (using Python threads)
- Each tool is called directly — faster and more debuggable than ReAct loop

Analogy: The Planner is the doctor who writes the prescription.
The Retriever is the pharmacist who fills it — exactly as written.
"""

import concurrent.futures
from typing import List, Dict, Callable
from langchain_openai import ChatOpenAI

from core.state import ResearchState, SubQueryRoute
from tools.web_search import tavily_web_search
from tools.arxiv_search import arxiv_search
from tools.vector_store import chroma_local_search


# Map tool name strings (from Planner JSON) to actual callable tool functions
TOOL_REGISTRY: Dict[str, Callable] = {
    "tavily_web_search": tavily_web_search,
    "arxiv_search":      arxiv_search,
    "chroma_local":      chroma_local_search,
}


def _execute_single_tool(tool_name: str, query: str, sub_query_context: str, api_keys: Dict[str, str] = None) -> List[Dict[str, str]]:
    """
    Execute one tool for one sub-query. Returns list of document dicts.

    Args:
        tool_name         : Key from TOOL_REGISTRY
        query             : The sub-query string to search
        sub_query_context : Original sub-query (attached to each doc for traceability)

    Returns:
        List of document dicts with 'source', 'content', 'sub_query', 'tool_used'
    """
    tool_fn = TOOL_REGISTRY.get(tool_name)
    if not tool_fn:
        print(f"[Retriever] Unknown tool '{tool_name}' — skipping.")
        return []

    try:
        print(f"[Retriever] Calling {tool_name} for: '{query}'")
        
        if tool_name == "tavily_web_search" and api_keys and "tavily" in api_keys:
            results = tool_fn.invoke({"query": query, "api_key": api_keys["tavily"]})
        else:
            results = tool_fn.invoke(query)  # LangChain @tool uses .invoke()

        # Normalize results — each tool returns List[Dict[source, content]]
        enriched = []
        for doc in results:
            if isinstance(doc, dict) and "content" in doc:
                enriched.append({
                    "source":    doc.get("source", "Unknown"),
                    "content":   doc.get("content", ""),
                    "sub_query": sub_query_context,
                    "tool_used": tool_name,
                })
        return enriched

    except Exception as e:
        print(f"[Retriever] Tool '{tool_name}' failed for query '{query}': {e}")
        return [{
            "source":    f"error:{tool_name}",
            "content":   f"Tool failed: {str(e)}",
            "sub_query": sub_query_context,
            "tool_used": tool_name,
        }]


def _execute_routed_sub_query(route: SubQueryRoute, api_keys: Dict[str, str] = None) -> List[Dict[str, str]]:
    """
    Execute ALL prescribed tools for ONE sub-query, in parallel if multiple tools.
    
    For a sub-query with tools = ["arxiv_search", "tavily_web_search"],
    both searches fire simultaneously via ThreadPoolExecutor.
    
    Args:
        route: SubQueryRoute dict with sub_query and tools list

    Returns:
        Combined list of docs from all tool calls
    """
    sub_query = route["sub_query"]
    tools     = route.get("tools", ["tavily_web_search"])  # Default to web search

    print(f"[Retriever] Sub-query: '{sub_query}' → Tools: {tools}")

    if len(tools) == 1:
        # Single tool — no parallelism needed, call directly
        return _execute_single_tool(tools[0], sub_query, sub_query, api_keys)

    # Multiple tools — fire them in parallel using threads
    # Analogy: Like sending multiple scouts in different directions simultaneously
    all_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(tools)) as executor:
        futures = {
            executor.submit(_execute_single_tool, tool_name, sub_query, sub_query, api_keys): tool_name
            for tool_name in tools
        }
        for future in concurrent.futures.as_completed(futures):
            tool_name = futures[future]
            try:
                results = future.result(timeout=30)  # 30s timeout per tool
                all_results.extend(results)
                print(f"[Retriever] ✓ {tool_name} returned {len(results)} docs")
            except concurrent.futures.TimeoutError:
                print(f"[Retriever] ✗ {tool_name} timed out — skipping")
            except Exception as e:
                print(f"[Retriever] ✗ {tool_name} raised exception: {e}")

    return all_results


def retriever_node(state: ResearchState, llm: ChatOpenAI) -> ResearchState:
    """
    Retriever node: executes each sub-query using its prescribed tool(s).
    
    Reads routing_plan from Planner, executes tools deterministically.
    No ReAct loop — pure, parallel, prescribed tool execution.

    Args:
        state: Current ResearchState (routing_plan must be populated)
        llm  : Not used directly, kept for signature consistency

    Returns:
        Updated state with raw_documents populated
    """
    routing_plan = state.get("routing_plan", [])
    api_keys = state.get("api_keys", {})

    if not routing_plan:
        print("[Retriever] No routing plan found — falling back to full query web search.")
        routing_plan = [{
            "sub_query": state["user_query"],
            "tools": ["tavily_web_search"],
            "rationale": "No routing plan available — defaulting to web search.",
        }]

    print(f"[Retriever] Executing {len(routing_plan)} routed sub-queries...")

    all_documents = []
    for i, route in enumerate(routing_plan):
        print(f"\n[Retriever] ── Sub-query {i+1}/{len(routing_plan)} ──")
        docs = _execute_routed_sub_query(route, api_keys)
        all_documents.extend(docs)
        print(f"[Retriever] Sub-query {i+1} total docs: {len(docs)}")

    print(f"\n[Retriever] Total documents collected: {len(all_documents)}")

    return {
        **state,
        "raw_documents": all_documents,
        "current_agent": "Dynamic Retriever ✅",
    }