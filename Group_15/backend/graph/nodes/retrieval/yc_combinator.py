import json
from utils.http import get_client
from graph.state import RepoItem


async def yc_combinator_retrieval(query: str) -> list[RepoItem]:
    """
    Uses YC's public Algolia search index (search-only key exposed in their JS bundle).
    This is a read-only public key intentionally shipped for client-side search.
    """
    client = get_client()

    try:
        response = await client.post(
            "https://45bwzj1sgc-dsn.algolia.net/1/indexes/WEB_PRODUCTION_COMPANIES/query",
            headers={
                "x-algolia-application-id": "45bwzj1sgc",
                "x-algolia-api-key": "Oa0057GFleOYa4uQUUCgR2GBjuEkdZXFOcnBHmqxHHI=",
                "content-type": "application/json",
            },
            content=json.dumps({
                "query": query,
                "hitsPerPage": 8,
                "attributesToRetrieve": [
                    "name", "one_liner", "long_description",
                    "url", "batch", "status", "slug", "tags"
                ]
            })
        )
        response.raise_for_status()
        data = response.json()

        hits = data.get("hits", [])
        items: list[RepoItem] = []

        for hit in hits:
            name = hit.get("name", "")
            one_liner = hit.get("one_liner", "")
            long_desc = (hit.get("long_description") or "")[:200]
            batch = hit.get("batch", "")
            slug = hit.get("slug", "")
            status = hit.get("status", "")

            url = f"https://www.ycombinator.com/companies/{slug}" if slug else ""
            summary = one_liner or long_desc or name

            if not name:
                continue

            items.append(RepoItem(
                source="yc",
                title=name,
                url=url,
                summary=summary[:200],
                relevance_score=0.0,
                metadata={"batch": batch, "status": status, "one_liner": one_liner}
            ))

        print(f"[YC] returned {len(items)} items for query: {query!r}")
        return items[:8]

    except Exception as e:
        print(f"[YC retrieval error] {e}")
        return []
