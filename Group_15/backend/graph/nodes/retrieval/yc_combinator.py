import os
import json
import pickle
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
from utils.http import get_client
from graph.state import RepoItem

# Cache paths
CACHE_DIR = Path(__file__).parent.parent.parent / ".cache"
YC_DATA_CACHE = CACHE_DIR / "yc_companies.json"
YC_EMBEDDINGS_CACHE = CACHE_DIR / "yc_embeddings.pkl"

# Global cache
_yc_data = None
_yc_embeddings = None
_embedding_model = None


def _get_embedding_model():
    """Load the embedding model (cached globally)."""
    global _embedding_model
    if _embedding_model is None:
        print("[YC RAG] Loading embedding model (one-time, ~90MB)...")
        # Using a small, fast model optimized for semantic search
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("[YC RAG] ✅ Embedding model loaded")
    return _embedding_model


async def _fetch_and_cache_yc_data():
    """Fetch YC companies and cache to disk."""
    global _yc_data

    # Check memory cache
    if _yc_data is not None:
        return _yc_data

    # Check disk cache
    if YC_DATA_CACHE.exists():
        print("[YC RAG] Loading companies from disk cache...")
        with open(YC_DATA_CACHE, 'r') as f:
            _yc_data = json.load(f)
        print(f"[YC RAG] ✅ Loaded {len(_yc_data)} companies from cache")
        return _yc_data

    # Fetch from API
    print("[YC RAG] Fetching companies from YC API (one-time download)...")
    client = get_client()

    try:
        response = await client.get(
            "https://yc-oss.github.io/api/companies/all.json",
            timeout=30.0
        )

        if response.status_code != 200:
            print(f"[YC RAG] Failed to fetch: {response.status_code}")
            return []

        companies = response.json()

        # Cache to disk
        CACHE_DIR.mkdir(exist_ok=True)
        with open(YC_DATA_CACHE, 'w') as f:
            json.dump(companies, f)

        _yc_data = companies
        print(f"[YC RAG] ✅ Downloaded and cached {len(companies)} companies")
        return companies

    except Exception as e:
        print(f"[YC RAG] Error fetching data: {e}")
        return []


def _create_embeddings(companies):
    """Create embeddings for all companies."""
    model = _get_embedding_model()

    # Create searchable text for each company
    texts = []
    for company in companies:
        name = company.get("name", "") or ""
        one_liner = company.get("one_liner", "") or ""
        long_desc = (company.get("long_description") or "")[:200]  # Limit length
        industry = company.get("industry", "") or ""
        tags = " ".join(company.get("tags", [])[:5])  # Top 5 tags

        # Combine into searchable text
        text = f"{name}. {one_liner}. {long_desc}. {industry}. {tags}"
        texts.append(text)

    print(f"[YC RAG] Creating embeddings for {len(texts)} companies...")
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)

    # Cache to disk
    with open(YC_EMBEDDINGS_CACHE, 'wb') as f:
        pickle.dump(embeddings, f)

    print("[YC RAG] ✅ Embeddings created and cached")
    return embeddings


def _load_or_create_embeddings(companies):
    """Load embeddings from cache or create if not exists."""
    global _yc_embeddings

    # Check memory cache
    if _yc_embeddings is not None:
        return _yc_embeddings

    # Check disk cache
    if YC_EMBEDDINGS_CACHE.exists():
        print("[YC RAG] Loading embeddings from cache...")
        with open(YC_EMBEDDINGS_CACHE, 'rb') as f:
            _yc_embeddings = pickle.load(f)
        print(f"[YC RAG] ✅ Loaded {len(_yc_embeddings)} embeddings from cache")
        return _yc_embeddings

    # Create new embeddings
    CACHE_DIR.mkdir(exist_ok=True)
    _yc_embeddings = _create_embeddings(companies)
    return _yc_embeddings


async def yc_combinator_retrieval(query: str) -> list[RepoItem]:
    """
    Retrieves Y Combinator companies using RAG (semantic search).

    First run: Downloads companies + creates embeddings (~30 seconds)
    Subsequent runs: Fast semantic search (~0.5 seconds)
    """

    # Fetch companies
    companies = await _fetch_and_cache_yc_data()
    if not companies:
        return []

    # Load/create embeddings
    embeddings = _load_or_create_embeddings(companies)

    # Embed the query
    model = _get_embedding_model()
    query_embedding = model.encode([query], convert_to_numpy=True)[0]

    # Compute cosine similarity
    similarities = np.dot(embeddings, query_embedding) / (
        np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
    )

    # Get top 8 most similar companies
    top_indices = np.argsort(similarities)[::-1][:8]

    items: list[RepoItem] = []

    for idx in top_indices:
        company = companies[idx]
        similarity_score = float(similarities[idx])

        # Filter out very low similarity matches
        if similarity_score < 0.2:
            continue

        name = company.get("name", "")
        one_liner = company.get("one_liner", "")
        long_desc = (company.get("long_description") or "")[:200]
        batch = company.get("batch", "")
        slug = company.get("slug", "")
        status = company.get("status", "")
        team_size = company.get("team_size", 0)
        website = company.get("website", "")

        url = f"https://www.ycombinator.com/companies/{slug}" if slug else website
        summary = one_liner or long_desc or name

        if not name:
            continue

        items.append(RepoItem(
            source="yc",
            title=name,
            url=url,
            summary=summary[:200],
            relevance_score=similarity_score,
            metadata={
                "batch": batch,
                "status": status,
                "one_liner": one_liner,
                "team_size": team_size,
                "website": website
            }
        ))

    print(f"[YC RAG] ✅ Returned {len(items)} companies (semantic search)")
    return items
