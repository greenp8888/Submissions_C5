from graph.state import GraphState


def input_node(state: GraphState) -> dict:
    idea = state.get("idea_description", "").strip()

    if not idea:
        return {"error": "idea_description is required"}

    if len(idea) > 500:
        return {"error": "idea_description must be under 500 characters"}

    return {
        "idea_description": idea,
        "audience": state.get("audience", "").strip(),
        "product_url": state.get("product_url", "").strip(),
        "error": None
    }
