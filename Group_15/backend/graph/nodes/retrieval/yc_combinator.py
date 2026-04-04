from bs4 import BeautifulSoup
from utils.http import get_client
from graph.state import RepoItem


async def yc_combinator_retrieval(query: str) -> list[RepoItem]:
    client = get_client()

    try:
        response = await client.get(
            "https://www.ycombinator.com/companies",
            params={"q": query}
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        items: list[RepoItem] = []

        company_cards = soup.select('a[href*="/companies/"]')[:8]

        for card in company_cards:
            company_name_elem = card.select_one('span, div, h3')
            company_name = company_name_elem.get_text(strip=True) if company_name_elem else ""

            tagline_elem = card.find_next('span', class_=lambda x: x and 'tagline' in x.lower()) if card else None
            if not tagline_elem:
                tagline_elem = card.select_one('.tagline, [class*="description"]')
            tagline = tagline_elem.get_text(strip=True) if tagline_elem else ""

            batch_elem = card.select_one('[class*="batch"]')
            batch = batch_elem.get_text(strip=True) if batch_elem else ""

            url = card['href'] if card.get('href') else ""
            if url and not url.startswith('http'):
                url = f"https://www.ycombinator.com{url}"

            if not company_name:
                continue

            items.append(RepoItem(
                source="yc",
                title=company_name,
                url=url,
                summary=tagline if tagline else company_name,
                relevance_score=0.0,
                metadata={"batch": batch, "status": "active"}
            ))

        return items[:8]

    except Exception as e:
        return []
