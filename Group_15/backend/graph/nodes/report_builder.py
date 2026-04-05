from graph.state import GraphState


def determine_traffic_light(matched_items: list, gap_analysis: list) -> tuple[str, str]:
    num_items = len(matched_items)
    num_gaps = len(gap_analysis)

    if num_items <= 5 and num_gaps >= 2:
        return "green", "Low competition with clear market gaps identified"
    elif num_items <= 10:
        return "amber", "Moderate competition exists with some differentiation opportunities"
    else:
        return "red", "Crowded market with limited differentiation potential"


def report_builder(state: GraphState) -> dict:
    print("\n" + "="*80)
    print("🔵 REPORT BUILDER - Assembling final report")
    print("="*80)

    matched_items = state.get("matched_items", [])
    analysis_data = state.get("analysis", {})

    gap_analysis = analysis_data.get("gap_analysis", [])
    suggested_features = analysis_data.get("suggested_features", [])
    competitive_landscape = analysis_data.get("competitive_landscape", "")
    sentiment = analysis_data.get("sentiment", {})
    market_signals = analysis_data.get("market_signals", [])

    traffic_light, traffic_light_reason = determine_traffic_light(matched_items, gap_analysis)

    sources_count = {}
    items_by_source = {}

    for item in matched_items:
        source = item["source"]
        sources_count[source] = sources_count.get(source, 0) + 1

        if source not in items_by_source:
            items_by_source[source] = []

        items_by_source[source].append({
            "title": item["title"],
            "url": item["url"],
            "summary": item["summary"],
            "relevance_score": item["relevance_score"],
            "metadata": item["metadata"]
        })

    executive_summary = f"{competitive_landscape}"

    report = {
        "executive_summary": executive_summary,
        "traffic_light": traffic_light,
        "traffic_light_reason": traffic_light_reason,
        "sources_count": sources_count,
        "features": suggested_features,
        "gap_analysis": gap_analysis,
        "items_by_source": items_by_source,
        "sentiment": sentiment,
        "competitive_landscape": competitive_landscape,
        "market_signals": market_signals
    }

    print("✅ Report assembled successfully:")
    print(f"  • Traffic light: {traffic_light.upper()} - {traffic_light_reason}")
    print(f"  • Total items in report: {len(matched_items)}")
    print(f"  • Gap analysis points: {len(gap_analysis)}")
    print(f"  • Suggested features: {len(suggested_features)}")
    print(f"  • Market signals: {len(market_signals)}")
    print("\n" + "="*80)
    print("✅ PIPELINE COMPLETE - Report ready for delivery")
    print("="*80 + "\n")

    return {"report": report}
