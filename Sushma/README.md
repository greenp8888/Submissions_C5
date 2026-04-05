# Multi-Agent AI Deep Researcher

A LangGraph-based multi-agent research system that orchestrates 5 specialized agents
to perform multi-hop, multi-source research investigations and compile structured reports.

## Key Features

- **5 Specialized Agents**: Query Planner, Retriever, Analyzer, Insight Generator, Report Builder
- **5 Retrieval Tools**: ArXiv, Tavily Web Search, Wikipedia, Google (SerpAPI), PDF loader
- **LangGraph StateGraph**: Shared `ResearchState` with conditional retry logic
- **Structured Reports**: Markdown reports with citations, contradictions, and insights
- **Input/Output Guardrails**: Validates queries and ensures report quality

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run the Agent

```bash
python -m multi_agent_researcher
```

Or programmatically:

```python
import asyncio
from multi_agent_researcher.main import run_research

async def research():
    report = await run_research("What are the latest advances in LLM reasoning?")
    print(report)

asyncio.run(research())
```

## Usage

Select a predefined scenario or enter a custom research query:

```
[1] Academic Research   — "What are the latest advances in LLM reasoning?"
[2] Current Events      — "What is happening with AI regulation in 2026?"
[3] Technical Deep-dive — "How does RAG compare to fine-tuning for domain adaptation?"
[4] Custom query
```

## Architecture

```
User Query
    │
    ▼
[Input Guardrail] — validates query + API keys
    │
    ▼
[Query Planner] — decomposes into sub-queries, selects sources
    │
    ▼
[Retriever] ←──────────────────────────────────────┐
    │                                               │
    ▼                                               │
{Enough data?} ──── No (attempt < 3) ──────────────┘
    │
    Yes
    │
    ▼
[Analyzer] — summarizes, finds contradictions, validates sources
    │
    ▼
[Insight Generator] — chain-of-thought hypotheses and trends
    │
    ▼
[Report Builder] — compiles final structured Markdown report
    │
    ▼
[Output Guardrail] — validates report quality
    │
    ▼
Final Report
```

## Project Structure

```
multi_agent_researcher/
├── main.py                    # Entry point, CLI menu, run_research()
├── utils/config.py            # load_config() from .env
├── models/
│   ├── state.py               # ResearchState TypedDict
│   ├── query.py               # ResearchQuery, SubQuery dataclasses
│   └── result.py              # RetrievalResult, ResearchReport
├── tools/
│   ├── arxiv_tools.py         # search_arxiv @tool
│   ├── tavily_tools.py        # tavily_web_search @tool
│   ├── wikipedia_tools.py     # wikipedia_search @tool
│   ├── serpapi_tools.py       # google_search @tool
│   └── pdf_tools.py           # load_pdf_document @tool
├── agents/
│   ├── query_planner.py       # Query decomposition node
│   ├── retriever.py           # Multi-source retrieval node
│   ├── analyzer.py            # Critical analysis node
│   ├── insight_generator.py   # Hypothesis generation node
│   └── report_builder.py      # Final report compilation node
├── graph/research_graph.py    # StateGraph construction
└── guardrails/
    ├── input_validation.py    # Pre-flight checks
    └── output_validation.py   # Report quality checks
```
