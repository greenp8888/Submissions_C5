"""
Generate a flow diagram from the compiled LangGraph graph.

Usage (from the backend/ directory):
    python generate_diagram.py

Outputs:
  - graph_diagram.png   — PNG image of the graph
  - graph_diagram.mmd   — Mermaid source (paste into README if preferred)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from graph.builder import build_graph

graph = build_graph()
print("Graph compiled successfully.")

# --- Mermaid text (always works, no extra deps) ---
mermaid_text = graph.get_graph().draw_mermaid()
Path("graph_diagram.mmd").write_text(mermaid_text)
print("Mermaid source written to graph_diagram.mmd")

# --- PNG via Mermaid.ink API (no local install required) ---
try:
    from langchain_core.runnables.graph import MermaidDrawMethod
    png_bytes = graph.get_graph().draw_mermaid_png(
        draw_method=MermaidDrawMethod.API
    )
    Path("graph_diagram.png").write_bytes(png_bytes)
    print("PNG diagram written to graph_diagram.png")
except Exception as e:
    print(f"PNG generation skipped ({e}). Use graph_diagram.mmd instead.")
