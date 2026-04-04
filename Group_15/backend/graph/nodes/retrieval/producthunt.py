import os
from bs4 import BeautifulSoup
from utils.http import get_client
from utils.llm import call_llm
from graph.state import RepoItem
from prompts.micro_summarize import micro_summarize_prompt


async def producthunt_retrieval(query: str) -> list[RepoItem]:
    client = get_client()

    try:
        response = await client.get(
            f"https://www.producthunt.com/search",
            params={"q": query}
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        items: list[RepoItem] = []

        product_cards = soup.select('[data-test="product-item"]')[:8]

        for i, card in enumerate(product_cards[:5]):
            title_elem = card.select_one('a[href*="/posts/"]')
            title = title_elem.get_text(strip=True) if title_elem else ""

            tagline_elem = card.select_one('[class*="tagline"]')
            tagline = tagline_elem.get_text(strip=True) if tagline_elem else ""

            votes_elem = card.select_one('[class*="vote"], [data-test*="vote"]')
            votes = 0
            if votes_elem:
                try:
                    votes = int(''.join(filter(str.isdigit, votes_elem.get_text())))
                except ValueError:
                    votes = 0

            link_elem = card.select_one('a[href*="/posts/"]')
            url = f"https://www.producthunt.com{link_elem['href']}" if link_elem and link_elem.get('href') else ""

            metadata = {
                "votes": votes,
                "tagline": tagline
            }

            content = f"{title}\n{tagline}"
            prompt = micro_summarize_prompt(title, content, "producthunt", metadata)

            try:
                summary = call_llm(prompt, max_tokens=256).strip()
            except Exception:
                summary = tagline[:150] if tagline else title

            items.append(RepoItem(
                source="ph",
                title=title,
                url=url,
                summary=summary,
                relevance_score=0.0,
                metadata=metadata
            ))

        for card in product_cards[5:]:
            title_elem = card.select_one('a[href*="/posts/"]')
            title = title_elem.get_text(strip=True) if title_elem else ""

            tagline_elem = card.select_one('[class*="tagline"]')
            tagline = tagline_elem.get_text(strip=True) if tagline_elem else ""

            votes_elem = card.select_one('[class*="vote"], [data-test*="vote"]')
            votes = 0
            if votes_elem:
                try:
                    votes = int(''.join(filter(str.isdigit, votes_elem.get_text())))
                except ValueError:
                    votes = 0

            link_elem = card.select_one('a[href*="/posts/"]')
            url = f"https://www.producthunt.com{link_elem['href']}" if link_elem and link_elem.get('href') else ""

            items.append(RepoItem(
                source="ph",
                title=title,
                url=url,
                summary=tagline if tagline else title,
                relevance_score=0.0,
                metadata={"votes": votes, "tagline": tagline}
            ))

        return items

    except Exception as e:
        return []
