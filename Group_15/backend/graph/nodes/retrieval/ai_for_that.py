import re
from bs4 import BeautifulSoup
from utils.http import get_client
from graph.state import RepoItem

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


async def ai_for_that_retrieval(query: str) -> list[RepoItem]:
    client = get_client()

    # URL-encode with hyphens (the site uses hyphenated slugs for search)
    slug_query = re.sub(r'\s+', '-', query.strip().lower())

    # Try two URL formats the site uses
    urls_to_try = [
        f"https://theresanaiforthat.com/s/{slug_query}/",
        f"https://theresanaiforthat.com/search/?q={query.replace(' ', '+')}",
    ]

    html = ""
    for url in urls_to_try:
        try:
            response = await client.get(url, headers=_HEADERS)
            if response.status_code == 200:
                html = response.text
                break
        except Exception:
            continue

    if not html:
        print(f"[ai4that] no response for query: {query!r}")
        return []

    soup = BeautifulSoup(html, "lxml")
    items: list[RepoItem] = []

    # TAAFT renders tool cards with several possible class patterns
    tool_cards = (
        soup.select('div[class*="ai_tool"]')
        or soup.select('div[class*="tool_wrap"]')
        or soup.select('div[class*="toolCard"]')
        or soup.select('.tool_item')
        or soup.select('[class*="tool-card"]')
        or soup.select('article[class*="tool"]')
        or soup.select('article')
    )

    for card in tool_cards[:8]:
        title_elem = card.select_one(
            'h2, h3, h4, .name, [class*="title"], [class*="name"]'
        )
        title = title_elem.get_text(strip=True) if title_elem else ""

        desc_elem = card.select_one(
            'p, .desc, [class*="description"], [class*="tagline"], [class*="summary"]'
        )
        description = desc_elem.get_text(strip=True)[:200] if desc_elem else ""

        link_elem = card.select_one('a[href]')
        url = link_elem.get("href", "") if link_elem else ""
        if url and not url.startswith("http"):
            url = f"https://theresanaiforthat.com{url}"

        if not title:
            continue

        items.append(RepoItem(
            source="ai4that",
            title=title,
            url=url,
            summary=description or title,
            relevance_score=0.0,
            metadata={},
        ))

    # Fallback: grab all internal tool links if no cards found
    if not items:
        for link in soup.select('a[href*="/ai/"]')[:8]:
            title = link.get_text(strip=True)
            href = link.get("href", "")
            if not href.startswith("http"):
                href = f"https://theresanaiforthat.com{href}"
            if title:
                items.append(RepoItem(
                    source="ai4that",
                    title=title,
                    url=href,
                    summary=title,
                    relevance_score=0.0,
                    metadata={},
                ))

    print(f"[ai4that] returned {len(items)} items for query: {query!r}")
    return items[:8]
