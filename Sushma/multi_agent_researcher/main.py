"""Multi-Agent AI Deep Researcher — Entry Point.

Orchestrates a multi-agent research pipeline using LangGraph's StateGraph
for graph-based orchestration and OpenRouter for LLM access. Supports
academic research, current events, and technical deep-dive scenarios.

Usage:
    python -m multi_agent_researcher
    # or
    python main.py  (from the Multi_Agent_cursor directory)
"""

import asyncio
import logging
import os
import ssl
import sys
from datetime import datetime, timezone

import httpx
import urllib3
from langchain_openai import ChatOpenAI

from multi_agent_researcher.graph.research_graph import build_research_graph
from multi_agent_researcher.guardrails.input_validation import validate_research_input
from multi_agent_researcher.guardrails.output_validation import validate_report_output
from multi_agent_researcher.models.state import ResearchState
from multi_agent_researcher.utils.config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------
# SSL workaround for Windows environments
# -----------------------------------------------------------------

def _apply_ssl_workaround() -> None:
    """Patch SSL verification for Windows systems that lack the required CA bundle.

    On Windows, Python's bundled certificate store often does not include
    the intermediate CAs used by api.openrouter.ai and api.tavily.com,
    causing SSLCertVerificationError on both httpx (OpenAI client) and
    requests (Tavily client). This patches both at the process level.

    This is safe for local development. For production, install proper
    CA certificates or use pip-system-certs to inherit the Windows store.
    """
    ssl._create_default_https_context = ssl._create_unverified_context
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    os.environ.setdefault("PYTHONHTTPSVERIFY", "0")
    os.environ.setdefault("CURL_CA_BUNDLE", "")
    logger.info("SSL workaround applied (verify=False) for local development")


# -----------------------------------------------------------------
# Predefined research scenarios
# -----------------------------------------------------------------

SCENARIOS = {
    "1": {
        "name": "Academic Research",
        "query": (
            "What are the latest advances in large language model reasoning, "
            "specifically chain-of-thought prompting and self-reflection techniques?"
        ),
    },
    "2": {
        "name": "Current Events",
        "query": (
            "What is happening with AI regulation in 2026? "
            "Which governments have passed or are considering AI legislation?"
        ),
    },
    "3": {
        "name": "Technical Deep-dive",
        "query": (
            "How does Retrieval-Augmented Generation (RAG) compare to "
            "fine-tuning for domain adaptation of large language models? "
            "What are the tradeoffs in accuracy, cost, and maintainability?"
        ),
    },
}


# -----------------------------------------------------------------
# LLM factory
# -----------------------------------------------------------------


def create_llm(config: dict) -> ChatOpenAI:
    """Create a ChatOpenAI instance pointed at OpenRouter.

    Args:
        config: Configuration dict from load_config().

    Returns:
        ChatOpenAI: Configured LLM for all agent nodes.

    Raises:
        SystemExit: If OPENROUTER_API_KEY is not set.
    """
    api_key = config.get("openrouter_api_key")
    if not api_key:
        print(
            "\n[ERROR] OPENROUTER_API_KEY not set.\n"
            "Add it to your .env file: OPENROUTER_API_KEY=your_key_here\n"
            "Get a key at: https://openrouter.ai"
        )
        sys.exit(1)

    base_url = config.get("openrouter_base_url", "https://openrouter.ai/api/v1")
    model_name = config.get("model_name", "openai/gpt-4.1-mini")

    # httpx clients with SSL verification disabled — required on Windows
    # where Python's CA bundle doesn't include OpenRouter's intermediate CA.
    http_client = httpx.Client(verify=False)
    http_async_client = httpx.AsyncClient(verify=False)

    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0.2,
        max_retries=1,
        http_client=http_client,
        http_async_client=http_async_client,
    )

    logger.info(
        "LLM configured: base_url=%s, model=%s", base_url, model_name
    )
    return llm


# -----------------------------------------------------------------
# Initial state factory
# -----------------------------------------------------------------


def build_initial_state(query: str, pdf_paths: list[str] | None = None) -> ResearchState:
    """Construct the initial ResearchState for a new research run.

    Args:
        query: The user's research question.
        pdf_paths: Optional list of local PDF file paths to include.

    Returns:
        ResearchState: Fully initialized state with all fields set to
            appropriate defaults for the pipeline entry point.
    """
    return ResearchState(
        query=query,
        sub_queries=[],
        sources_to_use=[],
        messages=[],
        retrieved_documents=[],
        analysis_summary="",
        contradictions=[],
        validated_sources=[],
        insights=[],
        final_report="",
        retrieval_attempts=0,
        status="initialized",
        pdf_paths=pdf_paths or [],
    )


# -----------------------------------------------------------------
# Main pipeline runner
# -----------------------------------------------------------------


async def run_research(
    query: str,
    pdf_paths: list[str] | None = None,
) -> str:
    """Run the full multi-agent research pipeline for a given query.

    Validates inputs, initializes state, invokes the LangGraph pipeline,
    validates outputs, and returns the final research report.

    Args:
        query: The user's research question.
        pdf_paths: Optional list of local PDF file paths to include.

    Returns:
        str: The final structured research report in Markdown format.
    """
    _apply_ssl_workaround()
    config = load_config()

    # --- Input Guardrail ---
    validation = validate_research_input(query, config)
    if not validation.valid:
        logger.error("Input validation failed: %s", validation.error)
        print(f"\n[INPUT VALIDATION FAILED]\n{validation.error}")
        return f"Research could not start.\n\nReason: {validation.error}"

    # --- Build LLM and Graph ---
    llm = create_llm(config)
    graph = build_research_graph(llm)

    # --- Initialize State ---
    initial_state = build_initial_state(query, pdf_paths)

    print("\n" + "=" * 60)
    print("  STARTING MULTI-AGENT RESEARCH PIPELINE")
    print("=" * 60)
    print(f"\nQuery: {query}\n")
    if pdf_paths:
        print(f"PDF sources: {len(pdf_paths)} file(s)\n")

    start_time = datetime.now(timezone.utc)

    # --- Execute Graph ---
    try:
        final_state = graph.invoke(initial_state)
    except Exception as exc:
        logger.error("Graph execution failed: %s", exc, exc_info=True)
        print(f"\n[PIPELINE ERROR] {exc}")
        return f"Research pipeline failed.\n\nError: {exc}"

    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    logger.info("Graph execution complete in %.1f seconds", elapsed)

    final_report = final_state.get("final_report", "")
    docs_retrieved = len(final_state.get("retrieved_documents", []))
    attempts = final_state.get("retrieval_attempts", 0)
    status = final_state.get("status", "unknown")

    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"  Status:      {status}")
    print(f"  Documents:   {docs_retrieved} retrieved")
    print(f"  Attempts:    {attempts} retrieval round(s)")
    print(f"  Time:        {elapsed:.1f}s")

    # --- Output Guardrail ---
    output_validation = validate_report_output(final_report, final_state)
    if not output_validation.valid:
        logger.warning("Output validation failed: %s", output_validation.error)
        print(f"\n[OUTPUT QUALITY WARNING] {output_validation.error}")
        # Return the report anyway — better partial output than nothing
        if final_report:
            print("  Returning partial report despite quality warning.")
        else:
            return f"Report generation failed.\n\nReason: {output_validation.error}"

    return final_report


# -----------------------------------------------------------------
# CLI entry point
# -----------------------------------------------------------------


async def main() -> None:
    """Main interactive entry point for the Multi-Agent Deep Researcher."""
    print("\n" + "=" * 60)
    print("  MULTI-AGENT AI DEEP RESEARCHER")
    print("=" * 60)
    print("\nSelect a research scenario or enter a custom query:\n")

    for key, scenario in SCENARIOS.items():
        print(f"  [{key}] {scenario['name']}")
        print(f"       {scenario['query'][:80]}...\n")

    print("  [4] Enter a custom research query")
    print("  [5] Enter a custom query + add PDF documents\n")

    choice = input("Select (1/2/3/4/5): ").strip()

    pdf_paths: list[str] = []

    match choice:
        case "1" | "2" | "3":
            query = SCENARIOS[choice]["query"]

        case "4":
            query = input("\nEnter your research query: ").strip()
            if not query:
                print("No query provided. Exiting.")
                return

        case "5":
            query = input("\nEnter your research query: ").strip()
            if not query:
                print("No query provided. Exiting.")
                return
            pdf_input = input(
                "Enter PDF file path(s) separated by semicolons (;): "
            ).strip()
            if pdf_input:
                pdf_paths = [p.strip() for p in pdf_input.split(";") if p.strip()]
                print(f"PDF files to include: {pdf_paths}")

        case _:
            print("Invalid choice. Exiting.")
            return

    report = await run_research(query, pdf_paths=pdf_paths)

    print("\n" + "=" * 60)
    print("  RESEARCH REPORT")
    print("=" * 60)
    print(report)

    # Offer to save the report
    save = input("\n\nSave report to file? (y/n): ").strip().lower()
    if save == "y":
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"research_report_{timestamp}.md"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"Report saved to: {filename}")
        except Exception as exc:
            print(f"Could not save report: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
