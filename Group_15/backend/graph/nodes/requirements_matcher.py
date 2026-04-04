import re
from datetime import datetime, timezone
from graph.state import GraphState, RepoItem


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
    raw_results = state.get("raw_results", {})
    idea = state["idea_description"]

    all_items: list[RepoItem] = []

    for source, items in raw_results.items():
        for item in items:
            text = f"{item['title']} {item['summary']}"

            keyword_score = compute_keyword_overlap(text, idea)
            recency_bonus = compute_recency_bonus(item["metadata"], item["source"])
            popularity = compute_popularity_signal(item["metadata"], item["source"])

            relevance_score = keyword_score + recency_bonus + popularity

            item["relevance_score"] = relevance_score
            all_items.append(item)

    # Keep any item with at least a minimal signal — stricter filtering happens in aggregator
    matched_items = [item for item in all_items if item["relevance_score"] >= 0.05]

    by_source: dict[str, int] = {}
    for item in matched_items:
        by_source[item["source"]] = by_source.get(item["source"], 0) + 1
    print(f"[matcher] {len(matched_items)} items passed threshold: {by_source}")

    return {"matched_items": matched_items}
