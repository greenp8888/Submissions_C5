from graph.state import GraphState


def input_node(state: GraphState) -> dict:
    print("\n" + "="*80)
    print("🔵 INPUT NODE - Validating input")
    print("="*80)

    idea = state.get("idea_description", "").strip()
    print(f"Idea: {idea[:100]}{'...' if len(idea) > 100 else ''}")

    if not idea:
        print("❌ ERROR: idea_description is required")
        return {"error": "idea_description is required"}

    if len(idea) > 500:
        print(f"❌ ERROR: idea_description too long ({len(idea)} chars)")
        return {"error": "idea_description must be under 500 characters"}

    audience = state.get("audience", "").strip()
    product_url = state.get("product_url", "").strip()

    print(f"Audience: {audience if audience else '(not specified)'}")
    print(f"Product URL: {product_url if product_url else '(not specified)'}")
    print("✅ Input validated successfully\n")

    return {
        "idea_description": idea,
        "audience": audience,
        "product_url": product_url,
        "error": None
    }
