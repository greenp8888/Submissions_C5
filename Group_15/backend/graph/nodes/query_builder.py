import json
from graph.state import GraphState
from prompts.query_builder import query_builder_prompt
from utils.llm import call_llm


def query_builder(state: GraphState) -> dict:
    prompt = query_builder_prompt(
        state["idea_description"],
        state.get("audience", ""),
        state.get("product_url", "")
    )

    try:
        content = call_llm(prompt, max_tokens=1024)
        query_object = json.loads(content)

        required_keys = {"github", "reddit", "hn", "ph", "ai4that", "yc"}
        if not all(k in query_object for k in required_keys):
            raise ValueError("Missing required query keys")

        return {"query_object": query_object}

    except (json.JSONDecodeError, ValueError) as e:
        idea = state["idea_description"]
        fallback_query = f"{idea[:50]}"

        return {
            "query_object": {
                "github": fallback_query,
                "reddit": fallback_query,
                "hn": fallback_query,
                "ph": fallback_query,
                "ai4that": fallback_query,
                "yc": fallback_query
            }
        }
