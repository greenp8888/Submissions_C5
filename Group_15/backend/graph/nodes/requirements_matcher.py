import re
import numpy as np
from datetime import datetime, timezone
from sentence_transformers import SentenceTransformer
from graph.state import GraphState, RepoItem

# Global embedding model for relevance filtering
_embedding_model = None


def _get_embedding_model():
    """Load embedding model for quick relevance filtering."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model


def quick_relevance_filter(items: list[RepoItem], idea: str, threshold: float = 0.25) -> list[RepoItem]:
    """
    Fast embedding-based relevance filter.
    Filters out obviously irrelevant items before detailed scoring.

    Args:
        items: All items to filter
        idea: User's idea description
        threshold: Minimum similarity score (0-1)

    Returns:
        Filtered list of potentially relevant items
    """
    if not items:
        return []

    model = _get_embedding_model()

    # Embed the user's idea
    idea_embedding = model.encode([idea], convert_to_numpy=True)[0]

    # Embed all item texts
    item_texts = [f"{item['title']} {item['summary']}" for item in items]
    item_embeddings = model.encode(item_texts, convert_to_numpy=True, show_progress_bar=False)

    # Compute cosine similarities
    similarities = np.dot(item_embeddings, idea_embedding) / (
        np.linalg.norm(item_embeddings, axis=1) * np.linalg.norm(idea_embedding)
    )

    # Filter by threshold
    filtered_items = []
    for item, similarity in zip(items, similarities):
        if similarity >= threshold:
            # Store embedding similarity for potential use in scoring
            item["embedding_similarity"] = float(similarity)
            filtered_items.append(item)

    return filtered_items


def compute_keyword_overlap(text: str, idea: str) -> float:
    text_lower = text.lower()
    idea_words = set(re.findall(r'\w+', idea.lower()))

    if not idea_words:
        return 0.0

    matches = sum(1 for word in idea_words if word in text_lower)
    return min(0.5, (matches / len(idea_words)) * 0.5)


def compute_recency_bonus(metadata: dict, source: str) -> float:
    now = datetime.now(timezone.utc)

    if source == "github":
        updated_at = metadata.get("updated_at", "")
        if updated_at:
            try:
                updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                days_old = (now - updated).days
                if days_old <= 365:
                    return 0.2
                elif days_old <= 730:
                    return 0.1
            except Exception:
                pass

    elif source == "reddit":
        created_utc = metadata.get("created_utc", 0)
        if created_utc:
            created = datetime.fromtimestamp(created_utc, tz=timezone.utc)
            days_old = (now - created).days
            if days_old <= 365:
                return 0.2
            elif days_old <= 730:
                return 0.1

    elif source == "hn":
        created_at = metadata.get("created_at", "")
        if created_at:
            try:
                created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                days_old = (now - created).days
                if days_old <= 365:
                    return 0.2
                elif days_old <= 730:
                    return 0.1
            except Exception:
                pass

    return 0.0


def compute_popularity_signal(metadata: dict, source: str) -> float:
    if source == "github":
        stars = metadata.get("stars", 0)
        return min(0.3, (stars / 10000) * 0.3)

    elif source == "reddit":
        score = metadata.get("score", 0)
        return min(0.3, (score / 1000) * 0.3)

    elif source == "hn":
        points = metadata.get("points", 0)
        return min(0.3, (points / 500) * 0.3)

    elif source == "ph":
        votes = metadata.get("votes", 0)
        return min(0.3, (votes / 500) * 0.3)

    return 0.0


def requirements_matcher(state: GraphState) -> dict:
    print("\n" + "="*80)
    print("🔵 REQUIREMENTS MATCHER - Two-stage filtering")
    print("="*80)

    raw_results = state.get("raw_results", {})
    idea = state["idea_description"]

    # Flatten all items
    all_items: list[RepoItem] = []
    for source, items in raw_results.items():
        all_items.extend(items)

    total_input = len(all_items)
    print(f"📥 Stage 1: Embedding-based pre-filter ({total_input} items)")

    # STAGE 1: Fast embedding-based relevance filter
    pre_filtered = quick_relevance_filter(all_items, idea, threshold=0.25)
    filtered_out_stage1 = total_input - len(pre_filtered)

    print(f"   ✅ Kept {len(pre_filtered)} items (filtered out {filtered_out_stage1} irrelevant)")
    print(f"\n📥 Stage 2: Detailed scoring ({len(pre_filtered)} items)")

    # STAGE 2: Detailed scoring on pre-filtered items
    scored_items: list[RepoItem] = []
    for item in pre_filtered:
        text = f"{item['title']} {item['summary']}"

        keyword_score = compute_keyword_overlap(text, idea)
        recency_bonus = compute_recency_bonus(item["metadata"], item["source"])
        popularity = compute_popularity_signal(item["metadata"], item["source"])

        # Boost score with embedding similarity (if available)
        embedding_bonus = item.get("embedding_similarity", 0) * 0.3

        relevance_score = keyword_score + recency_bonus + popularity + embedding_bonus

        item["relevance_score"] = relevance_score
        scored_items.append(item)

    # Keep items with minimal signal
    matched_items = [item for item in scored_items if item["relevance_score"] >= 0.05]

    by_source: dict[str, int] = {}
    for item in matched_items:
        by_source[item["source"]] = by_source.get(item["source"], 0) + 1

    total_filtered = total_input - len(matched_items)
    print(f"\n📊 Final results:")
    print(f"  • Stage 1 filtered: {filtered_out_stage1} items")
    print(f"  • Stage 2 filtered: {len(pre_filtered) - len(matched_items)} items")
    print(f"  • Total filtered: {total_filtered} items")
    print(f"  • Matched items: {len(matched_items)}")
    print(f"  • By source: {by_source}")

    if matched_items:
        avg_score = sum(item["relevance_score"] for item in matched_items) / len(matched_items)
        max_score = max(item["relevance_score"] for item in matched_items)
        print(f"  • Average score: {avg_score:.2f}")
        print(f"  • Highest score: {max_score:.2f}")
    print()

    return {"matched_items": matched_items}
