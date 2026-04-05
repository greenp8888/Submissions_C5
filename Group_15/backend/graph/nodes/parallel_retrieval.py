import asyncio
from graph.state import GraphState
from graph.nodes.retrieval.github import github_retrieval
from graph.nodes.retrieval.reddit import reddit_retrieval
from graph.nodes.retrieval.hackernews import hackernews_retrieval
from graph.nodes.retrieval.producthunt import producthunt_retrieval
from graph.nodes.retrieval.ai_for_that import ai_for_that_retrieval
from graph.nodes.retrieval.yc_combinator import yc_combinator_retrieval


async def parallel_retrieval_async(state: GraphState) -> dict:
    print("\n" + "="*80)
    print("🔵 PARALLEL RETRIEVAL - Fetching from 6 sources")
    print("="*80)

    query_object = state.get("query_object", {})

    print("🚀 Starting parallel fetches...")

    results = await asyncio.gather(
        github_retrieval(query_object.get("github", "")),
        reddit_retrieval(query_object.get("reddit", "")),
        hackernews_retrieval(query_object.get("hn", "")),
        producthunt_retrieval(query_object.get("ph", "")),
        ai_for_that_retrieval(query_object.get("ai4that", "")),
        yc_combinator_retrieval(query_object.get("yc", "")),
        return_exceptions=True
    )

    source_keys = ["github", "reddit", "hn", "ph", "ai4that", "yc"]
    raw_results = {}
    for key, result in zip(source_keys, results):
        if isinstance(result, Exception):
            print(f"[retrieval] {key} FAILED: {result}")
            raw_results[key] = []
        else:
            print(f"[retrieval] {key} → {len(result)} items")
            raw_results[key] = result

    print("\n📊 Retrieval Results:")
    total_items = 0
    source_names = ["github", "reddit", "hn", "ph", "ai4that", "yc"]

    for i, (source, items) in enumerate(raw_results.items()):
        count = len(items)
        total_items += count
        status = "✅" if count > 0 else "⚠️ "

        if isinstance(results[i], Exception):
            error_msg = f" ERROR: {type(results[i]).__name__}: {str(results[i])[:100]}"
            print(f"  {status} {source:10s}: {count} items - {error_msg}")
        else:
            print(f"  {status} {source:10s}: {count} items")

    print(f"\n✅ Total items retrieved: {total_items}\n")

    return {"raw_results": raw_results}


def parallel_retrieval(state: GraphState) -> dict:
    return asyncio.run(parallel_retrieval_async(state))
