import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import json
import uuid
import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from graph.builder import build_graph
from utils.cache import get_cached_report, cache_report

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
