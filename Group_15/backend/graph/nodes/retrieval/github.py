import os
from datetime import datetime
from utils.http import get_client
from utils.llm import call_llm
from graph.state import GraphState, RepoItem
from prompts.micro_summarize import micro_summarize_prompt


async def github_retrieval(query: str) -> list[RepoItem]:
    client = get_client()
    headers = {}

    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    else:
        print("[GitHub] Warning: No GITHUB_TOKEN set - rate limited to 60 requests/hour")

    try:
        response = await client.get(
            "https://api.github.com/search/repositories",
            params={"q": query, "sort": "stars", "per_page": 8},
            headers=headers
        )

        if response.status_code == 403:
            print(f"[GitHub] Rate limited! Status: {response.status_code}")
            print(f"[GitHub] Response: {response.text[:200]}")
            return []

        response.raise_for_status()
        data = response.json()

        if "items" not in data:
            print(f"[GitHub] No 'items' in response. Keys: {list(data.keys())}")
            print(f"[GitHub] Response preview: {str(data)[:200]}")
            return []

        repos = data.get("items", [])[:8]
        items: list[RepoItem] = []

        for i, repo in enumerate(repos[:3]):
            title = repo.get("full_name", "")
            description = repo.get("description", "") or ""

            metadata = {
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "language": repo.get("language", ""),
                "open_issues": repo.get("open_issues_count", 0),
                "updated_at": repo.get("updated_at", ""),
                "license": repo.get("license", {}).get("name", "") if repo.get("license") else ""
            }

            url = repo.get("html_url", "")

            prompt = micro_summarize_prompt(title, description, "github", metadata)

            try:
                summary = call_llm(prompt, max_tokens=256).strip()
            except Exception:
                summary = description[:150]

            items.append(RepoItem(
                source="github",
                title=title,
                url=url,
                summary=summary,
                relevance_score=0.0,
                metadata=metadata
            ))

        for repo in repos[3:]:
            title = repo.get("full_name", "")
            description = repo.get("description", "") or ""

            metadata = {
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "language": repo.get("language", ""),
                "open_issues": repo.get("open_issues_count", 0),
                "updated_at": repo.get("updated_at", ""),
                "license": repo.get("license", {}).get("name", "") if repo.get("license") else ""
            }

            items.append(RepoItem(
                source="github",
                title=title,
                url=repo.get("html_url", ""),
                summary=description[:150],
                relevance_score=0.0,
                metadata=metadata
            ))

        print(f"[GitHub] ✅ Returned {len(items)} repos for query: {query!r}")
        return items

    except Exception as e:
        print(f"❌ GitHub retrieval error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return []
