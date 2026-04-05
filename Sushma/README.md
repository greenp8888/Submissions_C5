# Multi-Agent AI Deep Researcher

An AI-powered research assistant that orchestrates five specialized agents to perform
multi-hop, multi-source investigations and compile structured, cited reports.

Built with **LangGraph**, **OpenRouter**, and a **Streamlit web UI**.

## Key Features

- **5 Specialized Agents**: Query Planner → Retriever → Analyzer → Insight Generator → Report Builder
- **5 Retrieval Sources**: ArXiv, Tavily Web Search, Wikipedia, Google (SerpAPI), PDF documents
- **LangGraph StateGraph**: Shared `ResearchState` with a conditional retry loop on the retriever
- **Streamlit UI**: Browser-based frontend with live progress, rendered report, and download
- **Input / Output Guardrails**: Validates queries before the graph and report quality after
- **OpenRouter LLM**: Use GPT-4o, Claude 3.5, Gemini, Llama 3.3, and more via one API key

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API keys

Copy the example file and fill in your keys:

```bash
copy .env.example .env
```

Minimum required (in `.env`):

```
OPENROUTER_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
```

Optional:

```
SERPAPI_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-4.1-mini
```

Get keys at:
- OpenRouter — https://openrouter.ai (required, LLM calls)
- Tavily — https://tavily.com (required, web search)
- SerpAPI — https://serpapi.com (optional, Google search)

## Running the App

### Option 1 — Streamlit UI (recommended)

```bash
streamlit run app.py
```

Opens at **http://localhost:8501**. The UI lets you:

- Pick from 3 predefined research scenarios with one click
- Enter any custom research question
- Upload PDF files as additional research sources
- Watch each agent's progress live as the pipeline runs
- Read the rendered Markdown report in the browser
- Download the final report as a `.md` file

> API keys can be entered directly in the sidebar — no `.env` file needed for quick testing.

### Option 2 — CLI

```bash
python -m multi_agent_researcher
```

Interactive menu:

```
[1] Academic Research   — Latest advances in LLM reasoning
[2] Current Events      — AI regulation in 2026
[3] Technical Deep-dive — RAG vs. fine-tuning
[4] Custom query
[5] Custom query + PDF documents
```

### Option 3 — Python API

```python
import asyncio
from multi_agent_researcher.main import run_research

async def main():
    report = await run_research(
        query="How does RAG compare to fine-tuning for domain adaptation?",
        pdf_paths=["path/to/paper.pdf"],  # optional
    )
    print(report)

asyncio.run(main())
```

## Project Structure

```
Multi_Agent_cursor/
├── app.py                          # Streamlit web UI
├── requirements.txt
├── .env.example
├── README.md
├── ARCHITECTURE.md                 # Architecture flowchart + code overview
│
└── multi_agent_researcher/
    ├── main.py                     # run_research() orchestrator, CLI menu, LLM factory
    ├── models/
    │   ├── state.py                # ResearchState TypedDict (shared LangGraph state)
    │   ├── query.py                # ResearchQuery, SubQuery dataclasses
    │   └── result.py               # RetrievalResult, AnalysisResult, ResearchReport
    ├── tools/
    │   ├── arxiv_tools.py          # search_arxiv @tool
    │   ├── tavily_tools.py         # tavily_web_search @tool
    │   ├── wikipedia_tools.py      # wikipedia_search @tool
    │   ├── serpapi_tools.py        # google_search @tool (graceful fallback if no key)
    │   └── pdf_tools.py            # load_pdf_document @tool
    ├── agents/
    │   ├── query_planner.py        # Decomposes query, selects sources
    │   ├── retriever.py            # Runs all tools per sub-query
    │   ├── analyzer.py             # Synthesizes evidence, finds contradictions
    │   ├── insight_generator.py    # Chain-of-thought hypotheses and trends
    │   └── report_builder.py       # Compiles final Markdown report
    ├── graph/
    │   └── research_graph.py       # StateGraph: nodes, edges, conditional retry edge
    ├── guardrails/
    │   ├── input_validation.py     # Query length + API key checks
    │   └── output_validation.py    # Report length, URL presence, heading structure
    └── utils/
        └── config.py               # load_config() — reads .env
```

## Predefined Scenarios

| # | Name | Query |
|---|---|---|
| 1 | Academic Research | Latest advances in LLM reasoning — chain-of-thought & self-reflection |
| 2 | Current Events | AI regulation in 2026 — government legislation worldwide |
| 3 | Technical Deep-dive | RAG vs. fine-tuning — accuracy, cost, and maintainability tradeoffs |

## Notes on Windows

On Windows, Python's CA bundle often does not trust the certificates used by
`api.openrouter.ai` and `api.tavily.com`. The project includes a built-in SSL
workaround (`main.py → _apply_ssl_workaround()`) that disables verification for
local development. This is applied automatically — no configuration needed.

For production use, install proper CA certificates or use `pip-system-certs` to
inherit the Windows certificate store.

## Architecture

For a detailed flowchart and file-by-file code overview, see [ARCHITECTURE.md](ARCHITECTURE.md).

```
User Query
    │
    ▼
[Input Guardrail] — validates query length + API keys
    │
    ▼
[Query Planner] — decomposes into 3–5 sub-queries, selects sources
    │
    ▼
[Retriever] ←─────────────────────────────────────────┐
    │                                                  │
    ▼                                                  │
{Sufficient coverage?} ── No (attempt < 3) ───────────┘
    │
    Yes
    │
    ▼
[Analyzer] — synthesizes evidence, flags contradictions, validates sources
    │
    ▼
[Insight Generator] — chain-of-thought hypotheses and trends
    │
    ▼
[Report Builder] — compiles structured Markdown report
    │
    ▼
[Output Guardrail] — validates report length, URLs, and headings
    │
    ▼
Final Report (rendered in browser or printed to terminal)
```
