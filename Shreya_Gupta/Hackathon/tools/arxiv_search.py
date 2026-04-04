"""
tools/arxiv_search.py — ArXiv Academic Paper Search Tool

USE THIS TOOL FOR:
- Physics, mathematics, computer science, quantitative biology/finance
- Peer-reviewed research and preprints
- Academic theories, formal proofs, scientific discoveries
- Keywords like: "Hawking radiation", "transformer architecture", "CRISPR mechanism"

DO NOT USE FOR:
- Current events or sports (use tavily_web_search)
- Content from user-uploaded PDFs (use chroma_local_search)

Analogy: This is your team's PhD librarian who has read every academic
paper published since 1991 and can pull the most relevant abstracts instantly.

ArXiv covers: Physics, Math, CS, Statistics, Biology, Finance, Economics.
It does NOT cover: Medical journals, law, humanities (for those, use Tavily).
"""

from typing import List, Dict
from langchain_core.tools import tool
import arxiv


@tool
def arxiv_search(query: str) -> List[Dict[str, str]]:
    """
    Search ArXiv for peer-reviewed academic papers and preprints.
    
    Best for: Scientific theories, academic research, technical papers,
    physics, mathematics, computer science, AI/ML research.
    NOT for: Real-time news, sports, celebrity info, or user-uploaded docs.
    
    Args:
        query: Academic search query. Use technical terminology for better results.
               Example: "Hawking radiation black hole information paradox 2024"
    
    Returns:
        List of dicts with 'source' (ArXiv URL) and 'content' (title + abstract)
    """
    try:
        client = arxiv.Client(
            page_size=5,
            delay_seconds=1.0,    # Be a good citizen — respect ArXiv rate limits
            num_retries=3,
        )

        search = arxiv.Search(
            query=query,
            max_results=5,
            sort_by=arxiv.SortCriterion.Relevance,
        )

        results = []
        for paper in client.results(search):
            # Format: Title + Authors + Abstract (truncated to ~800 chars)
            authors = ", ".join(str(a) for a in paper.authors[:3])
            if len(paper.authors) > 3:
                authors += " et al."

            content = (
                f"Title: {paper.title}\n"
                f"Authors: {authors}\n"
                f"Published: {paper.published.strftime('%Y-%m-%d')}\n"
                f"Abstract: {paper.summary[:800]}{'...' if len(paper.summary) > 800 else ''}"
            )

            results.append({
                "source": paper.entry_id,    # e.g., https://arxiv.org/abs/2310.12345
                "content": content,
            })

        return results if results else [
            {"source": "ArXiv", "content": f"No papers found for query: '{query}'. Try broader academic terminology."}
        ]

    except Exception as e:
        return [{"source": "error", "content": f"ArXiv search failed: {str(e)}"}]