import os
from graph.state import RepoItem
from utils.llm import call_llm
from prompts.micro_summarize import micro_summarize_prompt


async def producthunt_retrieval(query: str) -> list[RepoItem]:
    """
    Retrieves ProductHunt products using Tavily search API with domain filtering.
    This searches ProductHunt's content via web search for better relevance.
    Falls back to empty list if Tavily is not configured.
    """
    tavily_key = os.getenv("TAVILY_API_KEY")

    if not tavily_key:
        print("[ProductHunt] Tavily API key not set - skipping ProductHunt search")
        print("[ProductHunt] Add TAVILY_API_KEY to .env for ProductHunt results")
        return []

    try:
        from tavily import TavilyClient
    except ModuleNotFoundError:
        print(
            "[ProductHunt] Package tavily-python is not installed — skipping. "
            "Run: pip install tavily-python  (or pip install -r requirements.txt)"
        )
        return []

    try:
        client = TavilyClient(api_key=tavily_key)

        # Search specifically on ProductHunt domain
        response = client.search(
            query=f"{query} site:producthunt.com",
            search_depth="basic",
            max_results=10,
            include_domains=["producthunt.com"],
        )

        results = response.get("results", [])

        if not results:
            print(f"[ProductHunt] No results found for query: {query!r}")
            return []

        items: list[RepoItem] = []

        for result in results[:8]:
            title = result.get("title", "")
            url = result.get("url", "")
            content = result.get("content", "")
            score = result.get("score", 0.0)

            if not title or not url:
                continue

            # Skip non-product pages (homepage, about, etc.)
            # Accept both /posts/ and /products/ URLs
            if not any(x in url for x in ["/posts/", "/products/"]):
                continue

            # Extract product info from title (ProductHunt format: "Product - Description")
            if " - " in title:
                product_name = title.split(" - ")[0].strip()
                tagline = title.split(" - ", 1)[1].strip()
            else:
                product_name = title
                tagline = ""

            summary = content[:200] if content else tagline or product_name

            # Try to get votes from content if available
            votes = 0
            if "votes" in content.lower():
                import re
                vote_match = re.search(r'(\d+)\s*votes?', content.lower())
                if vote_match:
                    votes = int(vote_match.group(1))

            metadata = {
                "votes": votes,
                "tagline": tagline,
                "search_score": score
            }

            items.append(RepoItem(
                source="ph",
                title=product_name,
                url=url,
                summary=summary,
                relevance_score=float(score),
                metadata=metadata
            ))

        # LLM micro-summarize top 3 items
        enriched: list[RepoItem] = []
        for i, item in enumerate(items):
            if i < 3:
                try:
                    prompt = micro_summarize_prompt(
                        item["title"],
                        item["summary"],
                        "producthunt",
                        item["metadata"]
                    )
                    item["summary"] = call_llm(prompt, max_tokens=256).strip()
                except Exception:
                    pass
            enriched.append(item)

        print(f"[ProductHunt] ✅ Returned {len(enriched)} products for query: {query!r}")
        return enriched

    except Exception as e:
        print(f"❌ ProductHunt retrieval error: {type(e).__name__}: {str(e)}")
        return []
