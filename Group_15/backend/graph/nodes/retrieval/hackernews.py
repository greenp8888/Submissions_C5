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

        hits = data.get("hits", [])[:8]
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

        return items

    except Exception as e:
        return []
