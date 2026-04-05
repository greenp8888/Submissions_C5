import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import json
import re
import uuid
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from graph.builder import build_graph
from utils.llm import call_llm_async

load_dotenv()

app = FastAPI(title="SignalForge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()


class AnalyzeRequest(BaseModel):
    idea_description: str
    audience: str = ""
    product_url: str = ""


class TaglineRequest(BaseModel):
    idea_description: str


@app.post("/tagline")
async def tagline(req: TaglineRequest):
    prompt = (
        f"You are a product analyst. Given this idea: \"{req.idea_description}\"\n\n"
        f"Return a JSON object with exactly two fields:\n"
        f"1. \"tagline\": a 3-6 word catchy noun phrase naming the product category "
        f"(e.g. 'AI Meeting Summariser', 'Pet Health Monitor'). No punctuation, no quotes.\n"
        f"2. \"summary\": exactly 2 sentences explaining what this product does and the core problem it solves "
        f"for its target users. Be crisp and specific. No more than 2 sentences.\n\n"
        f"Return only valid JSON, no extra text."
    )
    raw = await call_llm_async(prompt, max_tokens=160)
    try:
        import json as _json
        parsed = _json.loads(raw.strip())
        return {"tagline": parsed.get("tagline", "").strip(), "summary": parsed.get("summary", "").strip()}
    except Exception:
        return {"tagline": raw.strip()[:80], "summary": ""}


@app.get("/sample-ideas")
async def sample_ideas(seed: str | None = Query(default=None, max_length=128)):
    """LLM-generated example prompts for the home page; `seed` varies output between loads."""
    nonce = (seed or "").strip() or str(uuid.uuid4())
    prompt = (
        "Generate exactly 4 creative, profitable, and timely product ideas worth building in 2026.\n\n"
        "Rules:\n"
        "- Each idea must be a single sentence (15–25 words) that describes the product clearly, "
        "written as an analysis prompt for an AI product intelligence tool.\n"
        "- Each idea must feel fresh and different — vary domains across B2B SaaS, mobile, marketplace, "
        "developer tools, consumer apps, climate, health, education, fintech, etc.\n"
        "- Avoid generic clichés; be specific. This batch must differ from typical AI-assistant or vague CRM ideas.\n"
        f"- Variation nonce (treat as unique; do not repeat prior batches): {nonce}\n"
        '- Include a 1–2 word ALL-CAPS category tag (e.g. "SAAS", "MOBILE", "B2B", "MARKETPLACE", '
        '"AI TOOL", "PLATFORM", "API").\n\n'
        "Return ONLY a valid JSON array — no markdown, no explanation:\n"
        "[\n"
        '  { "prompt": "...", "tag": "..." },\n'
        '  { "prompt": "...", "tag": "..." },\n'
        '  { "prompt": "...", "tag": "..." },\n'
        '  { "prompt": "...", "tag": "..." }\n'
        "]"
    )
    try:
        raw = await call_llm_async(prompt, max_tokens=512, temperature=1.12)
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```\s*$", "", cleaned).strip()
        ideas = json.loads(cleaned)
        if not isinstance(ideas, list) or len(ideas) == 0:
            return {"ideas": []}
        normalized = []
        for item in ideas[:4]:
            if isinstance(item, dict) and item.get("prompt"):
                normalized.append(
                    {"prompt": str(item["prompt"]).strip(), "tag": str(item.get("tag", "IDEA")).strip()}
                )
        return {"ideas": normalized}
    except Exception:
        return {"ideas": []}


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    # No in-memory report cache: a cache hit only emitted the final "report" SSE event,
    # so the UI skipped retrieval/matcher/analysis steps. Each run walks the full graph.

    request_id = str(uuid.uuid4())
    initial_state = {
        "idea_description": req.idea_description,
        "audience": req.audience,
        "product_url": req.product_url,
        "request_id": request_id,
        "error": None,
        "query_object": None,
        "raw_results": None,
        "matched_items": None,
        "analysis": None,
        "report": None
    }

    async def stream():
        async for event in graph.astream(initial_state, stream_mode="updates"):
            if event:
                node_name = list(event.keys())[0]
                update_data = event[node_name]
                yield f"data: {json.dumps({'node': node_name, 'update': update_data})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/health")
def health():
    return {"status": "ok"}
