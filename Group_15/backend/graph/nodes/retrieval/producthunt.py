import re
import json
from bs4 import BeautifulSoup
from utils.http import get_client
from utils.llm import call_llm
from graph.state import RepoItem
from prompts.micro_summarize import micro_summarize_prompt

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _parse_next_data(html: str) -> list[dict]:
    """Extract product list from Next.js __NEXT_DATA__ JSON blob."""
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html, re.DOTALL
    )
    if not match:
        return []
    try:
        nd = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []

    # Walk the props tree — PH's shape varies by deploy; try multiple paths
    props = nd.get("props", {}).get("pageProps", {})
    candidates = [
        props.get("posts"),
        props.get("results"),
        (props.get("searchResults") or {}).get("posts"),
        (props.get("searchResults") or {}).get("edges"),
        props.get("initialData"),
    ]
    for c in candidates:
        if isinstance(c, list) and c:
            return c
        if isinstance(c, dict):
            edges = c.get("edges") or c.get("items") or []
            if edges:
                return edges
    return []


async def producthunt_retrieval(query: str) -> list[RepoItem]:
    client = get_client()

    try:
        response = await client.get(
            "https://www.producthunt.com/search",
            params={"q": query},
            headers=_HEADERS,
        )
        response.raise_for_status()
        html = response.text

        items: list[RepoItem] = []

        # ── Strategy 1: extract from __NEXT_DATA__ ──────────────────────────
        raw_posts = _parse_next_data(html)
        for edge in raw_posts[:8]:
            node = edge.get("node", edge) if isinstance(edge, dict) else {}
            title = node.get("name") or node.get("title") or ""
            tagline = node.get("tagline") or node.get("description") or ""
            votes = node.get("votesCount") or node.get("votes_count") or 0
            slug = node.get("slug") or ""
            url = (
                f"https://www.producthunt.com/posts/{slug}"
                if slug
                else node.get("url") or node.get("website") or ""
            )
            if not title:
                continue
            items.append(RepoItem(
                source="ph",
                title=title,
                url=url,
                summary=tagline[:200] or title,
                relevance_score=0.0,
                metadata={"votes": votes, "tagline": tagline},
            ))

        # ── Strategy 2: BeautifulSoup fallback ──────────────────────────────
        if not items:
            soup = BeautifulSoup(html, "lxml")
            product_cards = (
                soup.select('[data-test="product-item"]')
                or soup.select('[class*="productItem"]')
                or soup.select('[class*="product-item"]')
                or soup.select('section[class*="post"]')
                or soup.select('li[class*="item"]')
            )
            for card in product_cards[:8]:
                link_elem = card.select_one('a[href*="/posts/"]')
                title_elem = card.select_one('h2, h3, h4') or link_elem
                title = title_elem.get_text(strip=True) if title_elem else ""
                tagline_elem = card.select_one(
                    'p, [class*="tagline"], [class*="description"]'
                )
                tagline = tagline_elem.get_text(strip=True) if tagline_elem else ""
                url = (
                    f"https://www.producthunt.com{link_elem['href']}"
                    if link_elem and link_elem.get("href")
                    else ""
                )
                if not title:
                    continue
                items.append(RepoItem(
                    source="ph",
                    title=title,
                    url=url,
                    summary=tagline[:200] or title,
                    relevance_score=0.0,
                    metadata={"votes": 0, "tagline": tagline},
                ))

        # ── LLM micro-summarise top 3 items ─────────────────────────────────
        enriched: list[RepoItem] = []
        for i, item in enumerate(items[:8]):
            if i < 3:
                try:
                    prompt = micro_summarize_prompt(
                        item["title"], item["summary"], "producthunt", item["metadata"]
                    )
                    item["summary"] = call_llm(prompt, max_tokens=256).strip()
                except Exception:
                    pass
            enriched.append(item)

        print(f"[ProductHunt] returned {len(enriched)} items for query: {query!r}")
        return enriched

    except Exception as e:
        print(f"[ProductHunt retrieval error] {e}")
        return []
