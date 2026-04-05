from graph.state import GraphState, RepoItem


def is_similar(title1: str, title2: str) -> bool:
    t1 = title1.lower().strip()
    t2 = title2.lower().strip()
    return t1 in t2 or t2 in t1


def aggregator(state: GraphState) -> dict:
    print("\n" + "="*80)
    print("🔵 AGGREGATOR - Deduplicating and sorting")
    print("="*80)

    matched_items = state.get("matched_items", [])
    print(f"📥 Input: {len(matched_items)} items")

    seen_urls: set[str] = set()
    seen_titles: list[str] = []
    deduped: list[RepoItem] = []

    duplicates_removed = 0
    for item in matched_items:
        url = item["url"]
        title = item["title"]

        if url in seen_urls:
            duplicates_removed += 1
            continue

        is_duplicate = any(is_similar(title, seen_title) for seen_title in seen_titles)
        if is_duplicate:
            duplicates_removed += 1
            continue

        seen_urls.add(url)
        seen_titles.append(title)
        deduped.append(item)

    print(f"  • Duplicates removed: {duplicates_removed}")
    print(f"  • After deduplication: {len(deduped)}")

    sorted_items = sorted(deduped, key=lambda x: x["relevance_score"], reverse=True)

    source_counts: dict[str, int] = {}
    final_items: list[RepoItem] = []

    for item in sorted_items:
        source = item["source"]
        count = source_counts.get(source, 0)

        if count < 5:
            final_items.append(item)
            source_counts[source] = count + 1

        if len(final_items) >= 20:
            break

    print(f"  • After diversity cap (max 5 per source, max 20 total): {len(final_items)}")
    print(f"\n📊 Final distribution by source:")
    for source, count in sorted(source_counts.items()):
        print(f"  • {source:10s}: {count} items")
    print()

    return {"matched_items": final_items}
