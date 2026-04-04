import os
from utils.http import get_client
from utils.llm import call_llm
from graph.state import RepoItem
from prompts.micro_summarize import micro_summarize_prompt


async def reddit_retrieval(query: str) -> list[RepoItem]:
    client = get_client()

    try:
        response = await client.get(
            "https://www.reddit.com/search.json",
            params={"q": query, "sort": "relevance", "limit": 10, "t": "year"}
        )
        response.raise_for_status()
        data = response.json()

        posts = data.get("data", {}).get("children", [])[:10]
        items: list[RepoItem] = []

        for i, post in enumerate(posts[:5]):
            post_data = post.get("data", {})
            title = post_data.get("title", "")
            selftext = post_data.get("selftext", "")[:300]

            metadata = {
                "score": post_data.get("score", 0),
                "num_comments": post_data.get("num_comments", 0),
                "subreddit": post_data.get("subreddit", ""),
                "created_utc": post_data.get("created_utc", 0)
            }

            permalink = post_data.get("permalink", "")
            url = f"https://www.reddit.com{permalink}" if permalink else ""

            content = f"{title}\n{selftext}"
            prompt = micro_summarize_prompt(title, content, "reddit", metadata)

            try:
                summary = call_llm(prompt, max_tokens=256).strip()
            except Exception:
                summary = selftext[:150] if selftext else title

            items.append(RepoItem(
                source="reddit",
                title=title,
                url=url,
                summary=summary,
                relevance_score=0.0,
                metadata=metadata
            ))

        for post in posts[5:]:
            post_data = post.get("data", {})
            title = post_data.get("title", "")
            selftext = post_data.get("selftext", "")[:150]

            metadata = {
                "score": post_data.get("score", 0),
                "num_comments": post_data.get("num_comments", 0),
                "subreddit": post_data.get("subreddit", ""),
                "created_utc": post_data.get("created_utc", 0)
            }

            permalink = post_data.get("permalink", "")
            url = f"https://www.reddit.com{permalink}" if permalink else ""

            items.append(RepoItem(
                source="reddit",
                title=title,
                url=url,
                summary=selftext if selftext else title,
                relevance_score=0.0,
                metadata=metadata
            ))

        return items

    except Exception as e:
        return []
