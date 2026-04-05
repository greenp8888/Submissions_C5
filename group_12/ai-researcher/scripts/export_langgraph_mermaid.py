#!/usr/bin/env python3
"""Emit LangGraph Mermaid for `build_graph()` (no API calls; needs OPENROUTER_API_KEY or .env)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Repo root = parent of scripts/
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from deep_researcher.config import Settings  # noqa: E402
from deep_researcher.graph import build_graph  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=_ROOT / "docs" / "images" / "langgraph_topology_compiled.mmd",
        help="Path for .mmd output",
    )
    args = p.parse_args()
    settings = Settings.load()
    compiled = build_graph(settings)
    mermaid = compiled.get_graph().draw_mermaid().strip()
    # LangGraph emits YAML frontmatter (flowchart curve) that mermaid-cli <11.6 rejects as parse error.
    if mermaid.startswith("---"):
        parts = mermaid.split("---", 2)
        if len(parts) >= 3 and "graph " in parts[2]:
            mermaid = parts[2].strip()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "%% Auto-generated from deep_researcher.graph.build_graph() — do not edit by hand.\n"
        "%% Regenerate: python scripts/export_langgraph_mermaid.py\n"
        "%% Render PNG: cd docs/images && npx -y @mermaid-js/mermaid-cli -i langgraph_topology_compiled.mmd "
        "-o langgraph_topology.png -w 3600 -H 2800 -b white\n\n"
        + mermaid
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
