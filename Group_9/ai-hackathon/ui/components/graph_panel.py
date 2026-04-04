from __future__ import annotations

import json


def render_graph(nodes: list[dict], edges: list[dict]) -> str:
    return "<pre>" + json.dumps({"nodes": nodes, "edges": edges}, indent=2) + "</pre>"

