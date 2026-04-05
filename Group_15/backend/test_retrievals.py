"""
Debug script to test each retrieval source individually
Run: python test_retrievals.py
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from graph.nodes.retrieval.github import github_retrieval
from graph.nodes.retrieval.reddit import reddit_retrieval
from graph.nodes.retrieval.hackernews import hackernews_retrieval
from graph.nodes.retrieval.producthunt import producthunt_retrieval
from graph.nodes.retrieval.ai_for_that import ai_for_that_retrieval
from graph.nodes.retrieval.yc_combinator import yc_combinator_retrieval


async def test_all():
    query = "AI email summarizer"

    print("\n" + "="*80)
    print("Testing all retrieval sources")
    print("="*80)
    print(f"Query: {query}\n")

    tests = [
        ("GitHub", github_retrieval),
        ("Reddit", reddit_retrieval),
        ("HackerNews", hackernews_retrieval),
        ("ProductHunt", producthunt_retrieval),
        ("AI For That", ai_for_that_retrieval),
        ("YC Combinator", yc_combinator_retrieval),
    ]

    for name, func in tests:
        print(f"\n{'='*80}")
        print(f"Testing {name}...")
        print('='*80)

        try:
            results = await func(query)
            print(f"✅ {name}: {len(results)} items retrieved")

            if results:
                print(f"\nFirst item:")
                print(f"  Title: {results[0]['title']}")
                print(f"  URL: {results[0]['url']}")
                print(f"  Summary: {results[0]['summary'][:100]}...")
            else:
                print(f"⚠️  No results returned (check for errors above)")

        except Exception as e:
            print(f"❌ {name} failed: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("Testing complete")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_all())
