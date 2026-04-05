from mcp.server.fastmcp import FastMCP
from googlesearch import search
from typing import List, Dict, Any
import hashlib

# 1. Initialize FastMCP Server
mcp = FastMCP("OpenSourceSearch", dependencies=["googlesearch-python"])

def _make_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:10]

# 2. Define the MCP Tool via decorator
@mcp.tool()
def open_source_web_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Perform a free, open-source web search using Google Search.
    Bypasses API key requirements and returns rich search results.
    """
    results = []
    try:
        # advanced=True allows us to get title, url, and description
        for r in search(query, num=max_results, stop=max_results, pause=2.0, advanced=True):
            print(f"[FastMCP] Found: {r.title}")
            results.append({
                "id": _make_id(r.url),
                "title": r.title,
                "url": r.url,
                "content": r.description[:500] if r.description else "",
                "snippet": r.description[:300] if r.description else "",
                "source_type": "web",
                "domain": r.url.split('/')[2] if '//' in r.url else r.url,
                "relevance_score": 0.6,
                "published_date": None
            })
    except Exception as e:
        print(f"[FastMCP] Web Search Error: {e}")
        
    return results

if __name__ == "__main__":
    # Start the server on stdio for LangChain integration
    mcp.run(transport='stdio')
