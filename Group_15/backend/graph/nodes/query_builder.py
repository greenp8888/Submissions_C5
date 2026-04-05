import json
from graph.state import GraphState
from prompts.query_builder import query_builder_prompt
from utils.llm import call_llm


def query_builder(state: GraphState) -> dict:
    print("\n" + "="*80)
    print("🔵 QUERY BUILDER - Generating search queries")
    print("="*80)

    prompt = query_builder_prompt(
        state["idea_description"],
        state.get("audience", ""),
        state.get("product_url", "")
    )

    idea = state["idea_description"]

    def fallback_queries() -> dict:
        print("🔄 Using fallback queries...")
        fallback_query = f"{idea[:50]}"
        print(f"  Fallback query: {fallback_query}\n")
        return {
            "query_object": {
                "github": fallback_query,
                "reddit": fallback_query,
                "hn": fallback_query,
                "ph": fallback_query,
                "ai4that": fallback_query,
                "yc": fallback_query,
            }
        }

    try:
        print("📡 Calling GPT-4.1 to generate queries...")
        content = call_llm(prompt, max_tokens=1024)
        query_object = json.loads(content)

        required_keys = {"github", "reddit", "hn", "ph", "ai4that", "yc"}
        if not all(k in query_object for k in required_keys):
            raise ValueError("Missing required query keys")

        print("✅ Queries generated successfully:")
        for source, query in query_object.items():
            print(f"  • {source:10s}: {query}")
        print()

        return {"query_object": query_object}

    except (json.JSONDecodeError, ValueError) as e:
        print(f"⚠️  LLM response parsing failed: {e}")
        return fallback_queries()

    except Exception as e:
        print(f"⚠️  Query builder LLM call failed (check OPENROUTER_API_KEY in backend/.env): {e}")
        return fallback_queries()
