import os
from utils.http import get_client
from utils.llm import call_llm
from graph.state import RepoItem
from prompts.micro_summarize import micro_summarize_prompt


async def hackernews_retrieval(query: str) -> list[RepoItem]:
    client = get_client()

    try:
        response = await client.get(
            "https://hn.algolia.com/api/v1/search",
            params={"query": query, "tags": "story", "hitsPerPage": 8}
        )
        response.raise_for_status()
        data = response.json()

        if "hits" not in data:
            print(f"[HN] No 'hits' in response. Keys: {list(data.keys())}")
            return []

        hits = data.get("hits", [])[:8]

        if not hits:
            print(f"[HN] Query returned 0 hits for: {query!r}")
        items: list[RepoItem] = []

        for i, hit in enumerate(hits[:5]):
            title = hit.get("title", "")
            story_text = hit.get("story_text", "") or ""
            story_text = story_text[:300]

            metadata = {
                "points": hit.get("points", 0),
                "num_comments": hit.get("num_comments", 0),
                "created_at": hit.get("created_at", ""),
                "author": hit.get("author", "")
            }

            url = hit.get("url", "") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"

            content = f"{title}\n{story_text}"
            prompt = micro_summarize_prompt(title, content, "hackernews", metadata)

            try:
                summary = call_llm(prompt, max_tokens=256).strip()
            except Exception:
                summary = story_text[:150] if story_text else title

            items.append(RepoItem(
                source="hn",
                title=title,
                url=url,
                summary=summary,
                relevance_score=0.0,
                metadata=metadata
            ))

        for hit in hits[5:]:
            title = hit.get("title", "")
            story_text = hit.get("story_text", "") or ""

            metadata = {
                "points": hit.get("points", 0),
                "num_comments": hit.get("num_comments", 0),
                "created_at": hit.get("created_at", ""),
                "author": hit.get("author", "")
            }

            url = hit.get("url", "") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"

            items.append(RepoItem(
                source="hn",
                title=title,
                url=url,
                summary=story_text[:150] if story_text else title,
                relevance_score=0.0,
                metadata=metadata
            ))

        print(f"[HN] ✅ Returned {len(items)} stories for query: {query!r}")
        return items

    except Exception as e:
        print(f"❌ HackerNews retrieval error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return []
