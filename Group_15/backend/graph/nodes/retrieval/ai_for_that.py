from bs4 import BeautifulSoup
from utils.http import get_client
from graph.state import RepoItem


async def ai_for_that_retrieval(query: str) -> list[RepoItem]:
    client = get_client()

    try:
        url_query = query.replace(" ", "%20")
        response = await client.get(f"https://theresanaiforthat.com/s/{url_query}/")
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        items: list[RepoItem] = []

        tool_cards = soup.select('.tool-card, [class*="tool"], article')[:8]

        for card in tool_cards:
            title_elem = card.select_one('h2, h3, .title, [class*="name"]')
            title = title_elem.get_text(strip=True) if title_elem else ""

            desc_elem = card.select_one('p, .description, [class*="desc"]')
            description = desc_elem.get_text(strip=True) if desc_elem else ""

            category_elem = card.select_one('.category, [class*="category"]')
            category = category_elem.get_text(strip=True) if category_elem else ""

            link_elem = card.select_one('a[href]')
            url = link_elem['href'] if link_elem and link_elem.get('href') else ""
            if url and not url.startswith('http'):
                url = f"https://theresanaiforthat.com{url}"

            if not title:
                continue

            items.append(RepoItem(
                source="ai4that",
                title=title,
                url=url,
                summary=description[:150] if description else title,
                relevance_score=0.0,
                metadata={"category": category}
            ))

        return items[:8]

    except Exception as e:
        return []
