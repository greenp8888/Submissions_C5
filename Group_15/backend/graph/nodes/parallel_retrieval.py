import asyncio
from graph.state import GraphState
from graph.nodes.retrieval.github import github_retrieval
from graph.nodes.retrieval.reddit import reddit_retrieval
from graph.nodes.retrieval.hackernews import hackernews_retrieval
from graph.nodes.retrieval.producthunt import producthunt_retrieval
from graph.nodes.retrieval.ai_for_that import ai_for_that_retrieval
from graph.nodes.retrieval.yc_combinator import yc_combinator_retrieval


async def parallel_retrieval_async(state: GraphState) -> dict:
    query_object = state.get("query_object", {})

    results = await asyncio.gather(
        github_retrieval(query_object.get("github", "")),
        reddit_retrieval(query_object.get("reddit", "")),
        hackernews_retrieval(query_object.get("hn", "")),
        producthunt_retrieval(query_object.get("ph", "")),
        ai_for_that_retrieval(query_object.get("ai4that", "")),
        yc_combinator_retrieval(query_object.get("yc", "")),
        return_exceptions=True
    )

    raw_results = {
        "github": results[0] if not isinstance(results[0], Exception) else [],
        "reddit": results[1] if not isinstance(results[1], Exception) else [],
        "hn": results[2] if not isinstance(results[2], Exception) else [],
        "ph": results[3] if not isinstance(results[3], Exception) else [],
        "ai4that": results[4] if not isinstance(results[4], Exception) else [],
        "yc": results[5] if not isinstance(results[5], Exception) else [],
    }

    return {"raw_results": raw_results}


def parallel_retrieval(state: GraphState) -> dict:
    return asyncio.run(parallel_retrieval_async(state))
