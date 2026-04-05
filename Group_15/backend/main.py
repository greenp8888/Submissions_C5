import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import json
import uuid
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from graph.builder import build_graph
from utils.cache import get_cached_report, cache_report
from utils.llm import call_llm_async

load_dotenv()

app = FastAPI(title="Ideascope API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
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


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    cached = get_cached_report(req.idea_description, req.audience)
    if cached:
        async def cached_stream():
            yield f"data: {json.dumps({'node': 'report', 'update': {'report': cached}})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(cached_stream(), media_type="text/event-stream")

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
        final_report = None
        async for event in graph.astream(initial_state, stream_mode="updates"):
            if event:
                node_name = list(event.keys())[0]
                update_data = event[node_name]

                if node_name == "report" and "report" in update_data:
                    final_report = update_data["report"]

                yield f"data: {json.dumps({'node': node_name, 'update': update_data})}\n\n"

        if final_report:
            cache_report(req.idea_description, req.audience, final_report)

        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/health")
def health():
    return {"status": "ok"}
