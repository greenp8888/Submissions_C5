"""
=============================================================================
Main Entry Point — CLI
=============================================================================
Usage:
    python main.py --query "What are the latest advances in quantum computing?"
    python main.py --query "..." --depth deep
    python main.py --query "..." --output results.json
    python main.py --query "..." --export-report report.md
=============================================================================
"""
import argparse
import json
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from agents.orchestrator import run_pipeline
from config import settings

console = Console()
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL if hasattr(settings, "LOG_LEVEL") else "INFO"),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)


def display_results(state: dict):
    """Pretty-print pipeline results using Rich."""

    console.print()
    console.print(Panel.fit(
        "[bold cyan]🔬 Deep Research Results[/bold cyan]",
        border_style="cyan",
    ))

    # ── Metrics ──
    metrics_table = Table(title="Pipeline Summary", show_lines=True)
    metrics_table.add_column("Metric", style="bold")
    metrics_table.add_column("Value", justify="center")
    metrics_table.add_row("Sources Retrieved", str(len(state.get("sources", []))))
    metrics_table.add_row("Sub-Questions", str(len(state.get("sub_questions", []))))
    metrics_table.add_row("Fact Checks", str(len(state.get("fact_checks", []))))
    metrics_table.add_row("Overall Reliability", f"{state.get('overall_reliability', 0):.0%}")
    metrics_table.add_row("Trends Found", str(len(state.get("trends", []))))
    metrics_table.add_row("Hypotheses Generated", str(len(state.get("hypotheses", []))))
    metrics_table.add_row("Retrieval Rounds", str(state.get("retrieval_round", 0)))
    metrics_table.add_row("Contradictions", str(len(state.get("contradictions", []))))
    metrics_table.add_row("Information Gaps", str(len(state.get("information_gaps", []))))
    console.print(metrics_table)

    # ── Query Plan ──
    sub_qs = state.get("sub_questions", [])
    if sub_qs:
        sq_table = Table(title="Research Sub-Questions")
        sq_table.add_column("#", width=3)
        sq_table.add_column("Priority", width=8)
        sq_table.add_column("Question", width=70)
        for sq in sub_qs:
            sq_table.add_row(
                str(sq.get("id", "?")),
                f"P{sq.get('priority', '?')}",
                sq.get("question", "N/A")[:70],
            )
        console.print(sq_table)

    # ── Sources ──
    sources = state.get("sources", [])
    if sources:
        src_table = Table(title=f"Sources ({len(sources)})")
        src_table.add_column("ID", width=12)
        src_table.add_column("Type", width=10)
        src_table.add_column("Title", width=50)
        src_table.add_column("Relevance", width=10)
        for s in sources[:20]:
            src_table.add_row(
                s.get("id", "?"),
                s.get("source_type", "?"),
                s.get("title", "Untitled")[:50],
                f"{s.get('relevance_score', 0):.0%}",
            )
        console.print(src_table)

    # ── Key Takeaways ──
    takeaways = state.get("key_takeaways", [])
    if takeaways:
        console.print(Panel(
            "\n".join(f"💡 {t}" for t in takeaways),
            title="Key Takeaways",
            border_style="green",
        ))

    # ── Fact Checks ──
    fact_checks = state.get("fact_checks", [])
    if fact_checks:
        fc_table = Table(title="Fact Check Results")
        fc_table.add_column("Status", width=20)
        fc_table.add_column("Claim", width=55)
        fc_table.add_column("Confidence", width=12)
        for fc in fact_checks:
            status = fc.get("status", "?")
            style = {
                "VERIFIED": "green",
                "PARTIALLY_VERIFIED": "yellow",
                "UNVERIFIED": "dim",
                "CONTRADICTED": "red",
            }.get(status, "")
            fc_table.add_row(
                status, fc.get("claim", "?")[:55],
                f"{fc.get('confidence', 0):.0%}",
                style=style,
            )
        console.print(fc_table)

    # ── Trends ──
    trends = state.get("trends", [])
    if trends:
        console.print(f"\n[bold]📈 Trends ({len(trends)}):[/bold]")
        for t in trends:
            console.print(f"  [{t.get('confidence', '?')}] {t.get('title', '?')}: {t.get('description', '')[:80]}")

    # ── Hypotheses ──
    hypotheses = state.get("hypotheses", [])
    if hypotheses:
        console.print(f"\n[bold]🧪 Hypotheses ({len(hypotheses)}):[/bold]")
        for h in hypotheses:
            console.print(f"  • {h.get('statement', '?')[:90]}")
            chain = h.get("reasoning_chain", [])
            for i, step in enumerate(chain[:3], 1):
                console.print(f"    {i}. {step[:80]}")

    # ── Synthesis ──
    narrative = state.get("synthesis_narrative", "")
    if narrative:
        console.print(Panel(narrative[:500], title="Synthesis Narrative", border_style="blue"))

    # ── Report Preview ──
    report = state.get("report", {})
    if report:
        console.print(Panel(
            report.get("executive_summary", "No executive summary")[:400],
            title=f"📝 Report: {report.get('title', 'Untitled')}",
            border_style="cyan",
        ))

    # ── Errors ──
    errors = state.get("error_trace", [])
    if errors:
        console.print(Panel("\n".join(errors), title="❌ Errors", border_style="red"))

    console.print(f"\n[bold]Pipeline Status:[/bold] {state.get('pipeline_status', 'unknown')}")


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent AI Deep Researcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --query "What are the latest advances in quantum error correction?"
  python main.py --query "How is AI used in drug discovery?" --depth deep
  python main.py --query "..." --output results.json --export-report report.md
        """,
    )
    parser.add_argument("--query", "-q", required=True, help="Research question")
    parser.add_argument("--depth", "-d", choices=["quick", "standard", "deep"],
                        default="standard", help="Research depth")
    parser.add_argument("--output", "-o", help="Save full state to JSON file")
    parser.add_argument("--export-report", "-r", help="Export report to Markdown file")

    args = parser.parse_args()

    # Validate config
    issues = settings.validate()
    if issues:
        console.print("[yellow]⚠️ Configuration warnings:[/yellow]")
        for issue in issues:
            console.print(f"  - {issue}")

    # Run
    final_state = run_pipeline(query=args.query, depth=args.depth)

    # Display
    display_results(final_state)

    # Save state
    if args.output:
        Path(args.output).write_text(json.dumps(final_state, indent=2, default=str))
        console.print(f"\n💾 Full state saved to {args.output}")

    # Export report
    if args.export_report:
        report_md = final_state.get("report_markdown", "")
        if report_md:
            Path(args.export_report).write_text(report_md)
            console.print(f"📝 Report exported to {args.export_report}")
        else:
            console.print("[yellow]No report to export[/yellow]")


if __name__ == "__main__":
    main()
