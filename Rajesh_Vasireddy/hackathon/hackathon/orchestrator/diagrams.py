"""
Standalone utility – exports the incident-pipeline flowchart as HTML and Markdown.

Run directly:
    python orchestrator/diagrams.py

Outputs (written next to this file):
    pipeline.html  – open in any browser to see the rendered diagram
    pipeline.md    – Mermaid fenced block, renderable in GitHub / VS Code preview
"""

from __future__ import annotations

from pathlib import Path

GRAPH = """\
flowchart TD
    START([START]) --> log_reader
    log_reader["log_reader_agent\\nParse logs, extract ERROR/CRITICAL"]
    log_reader --> check1{status == failed?}
    check1 -- yes --> END1([END])
    check1 -- no --> remediation
    remediation["remediation_agent\\nLLM analyses errors, suggests fixes"]
    remediation --> check2{status == failed?}
    check2 -- yes --> END2([END])
    check2 -- no --> cookbook
    cookbook["cookbook_agent\\nGenerate runbook / reference guide"]
    cookbook --> jira
    jira["jira_agent\\nAuto-create Jira incident ticket"]
    jira --> slack
    slack["slack_agent\\nSend Slack incident alert"]
    slack --> END3([END])
"""

_HERE = Path(__file__).resolve().parent


def save_html(output_path: Path = _HERE / "pipeline.html") -> Path:
    """Write an HTML file that renders the diagram via mermaid.js CDN."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Incident Pipeline Diagram</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({{startOnLoad: true, theme: 'default'}});</script>
  <style>
    body {{ font-family: sans-serif; padding: 2rem; background: #f5f5f5; }}
    h1   {{ color: #333; }}
    .mermaid {{ background: #fff; padding: 1.5rem; border-radius: 8px;
               box-shadow: 0 2px 8px rgba(0,0,0,.1); }}
  </style>
</head>
<body>
  <h1>Incident Pipeline Flowchart</h1>
  <div class="mermaid">
{GRAPH}
  </div>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")
    print(f"Saved HTML  → {output_path}")
    return output_path


def save_markdown(output_path: Path = _HERE / "pipeline.md") -> Path:
    """Write a Markdown file with a mermaid fenced code block."""
    md = f"# Incident Pipeline Flowchart\n\n```mermaid\n{GRAPH}\n```\n"
    output_path.write_text(md, encoding="utf-8")
    print(f"Saved Markdown → {output_path}")
    return output_path


if __name__ == "__main__":
    save_html()
    save_markdown()
