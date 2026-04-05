# Lumeris — Research Intelligence System

> **Illuminating the path from data to discovery!**

A single-file, production-ready multi-agent AI research assistant built with **LangGraph** and **Streamlit**. Lumeris decomposes complex queries into structured sub-questions, orchestrates parallel tool retrieval across Wikipedia, ArXiv, and the web, performs semantic search over your own PDFs, and synthesises everything into a verified, auditable research report.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Agent Pipeline](#agent-pipeline)
- [Retrieval Tools](#retrieval-tools)
- [PDF RAG Engine](#pdf-rag-engine)
- [Shared State](#shared-state)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the App](#running-the-app)
- [Using the Interface](#using-the-interface)
- [Output and Exports](#output-and-exports)
- [Token Tracking and Cost Estimation](#token-tracking-and-cost-estimation)
- [Audit Trail](#audit-trail)
- [Error Handling and Fallbacks](#error-handling-and-fallbacks)
- [Supported Models](#supported-models)
- [Project Structure](#project-structure)
- [Requirements](#requirements)

---

## Overview

Lumeris wraps a full research workflow — from initial query decomposition through to a structured, cited report — inside a single Python file. The orchestration layer is built on **LangGraph**, which manages a typed shared state object (`ResearchState`) as it flows through seven specialised agents in sequence. A **Streamlit** frontend provides an interactive UI for query input, investigation path selection, live pipeline status, and report display.

When LangGraph is available, the compiled state machine executes the full pipeline automatically. If LangGraph is not installed, the agents fall back to sequential manual execution with the same result.

---

## Key Features

**Multi-agent orchestration** — Seven specialised agents collaborate through a shared typed state. Each agent reads from and writes to `ResearchState`, ensuring every downstream agent has full context.

**Parallel retrieval** — The Retriever agent dispatches tool calls concurrently using `ThreadPoolExecutor` (up to 5 workers), so Wikipedia, ArXiv, and Tavily results arrive simultaneously rather than waiting in sequence.

**PDF RAG support** — Upload any PDF from the sidebar. The system extracts text, splits it into 400-character chunks with 50-character overlap, generates lightweight bag-of-words embeddings, and builds a FAISS flat index for semantic retrieval at query time. No external embedding model is required.

**Critical analysis** — The Analyst agent synthesises retrieved content, detects contradictions between sources, and assigns a confidence score. Contradictions are surfaced explicitly in the final report.

**Red team validation** — A dedicated agent reviews the analysis and insights for hallucinations, bias, and logical gaps. Identified issues are flagged with severity levels and carried through to the report.

**Iterative gap-fill** — After red-team validation, the Gap-fill agent re-runs targeted retrieval queries against any data gaps identified by either the Analyst or the Red Team agent, merging results back into the main evidence corpus.

**Full audit trail** — Every agent logs timestamped entries with pass/fail status to a persistent audit trail displayed in the right-hand panel throughout execution.

**Token tracking and cost estimation** — Running token counts and estimated costs are tracked per session and displayed in the UI for each supported model.

**PDF export** — Final reports can be exported as formatted PDFs using ReportLab, or as JSON if ReportLab is unavailable.

---

## Architecture

```
User Query
    │
    ▼
┌─────────────┐
│   Planner   │  Decomposes query into sub-questions and investigation paths
└──────┬──────┘
       │
    ┌──▼──────────────────────────────────────┐
    │              Retriever                  │
    │  ┌──────────┬──────────┬─────────────┐  │
    │  │Wikipedia │  ArXiv   │Tavily Search│  │  ← ThreadPoolExecutor (parallel)
    │  └──────────┴──────────┴─────────────┘  │
    │  ┌──────────────────────────────────┐   │
    │  │  PDF RAG (FAISS) — if uploaded   │   │  ← conditional
    │  └──────────────────────────────────┘   │
    └──────────────────┬──────────────────────┘
                       │
               ┌───────▼────────┐
               │    Analyst     │  Synthesis, contradiction detection, confidence scoring
               └───────┬────────┘
                       │
               ┌───────▼────────┐
               │    Insight     │  Trends, risks, opportunities, hypotheses
               └───────┬────────┘
                       │
               ┌───────▼────────┐
               │   Red Team     │  Hallucination flags, bias detection, logical gaps
               └───────┬────────┘
                       │
               ┌───────▼────────┐
               │   Gap Fill     │  Iterative retrieval for identified gaps
               └───────┬────────┘
                       │
               ┌───────▼────────┐
               │    Reporter    │  Structured report, evidence table, citations
               └───────┬────────┘
                       │
                  Final Report
```

The LangGraph state machine is compiled via `build_graph(cfg)` and defines the following edges:

```
planner → retriever → analyst → insight → red_team → gap_fill → reporter → END
```

---

## Agent Pipeline

### 1. Planner agent

**Entry point.** Receives the raw user query and calls the LLM to decompose it into:

- A list of focused **sub-questions**, each with a priority (`high`, `med`, `low`) and reasoning.
- Two or more **investigation paths**, each specifying a name, focus, description, and which tools to use.

The user selects an investigation path from the UI before the full pipeline runs. The selected path is stored on `ResearchState.selected_path` and used by the Retriever to determine its tool mix.

### 2. Retriever agent

Reads the selected investigation path and sub-questions from state, then builds a list of tool query objects. These are dispatched in parallel via `run_tools_parallel()`:

- Each query specifies a tool (`wikipedia`, `arxiv`, or `tavily`) and a query string.
- Up to 5 workers run concurrently using `ThreadPoolExecutor`.
- Results from all sources are merged into `ResearchState.retrieval_results`.

If a PDF has been uploaded and indexed, the Retriever also runs `rag_search()` against the FAISS index for each sub-question and the investigation focus query. RAG results are stored separately in `ResearchState.rag_results` and merged into the main corpus.

### 3. Analysis agent

Receives the full retrieval corpus (web + RAG results) and prompts the LLM to produce:

- An executive **summary** of the corpus relative to the query.
- A list of **key findings**.
- Any **contradictions** detected between sources, with descriptions of the conflicting claims.
- **Data gaps** — areas where the evidence is thin or missing.
- A **confidence score** (0–1) reflecting the overall reliability of the corpus.

The structured JSON output is stored in `ResearchState.analysis`.

### 4. Insight agent

Reads the analysis summary and key findings to generate forward-looking intelligence:

- **Trends** — patterns and trajectories in the evidence.
- **Risks** — potential downsides or concerns.
- **Opportunities** — areas for action or further investigation.
- **Hypotheses** — plausible explanations warranting further research.
- **Strategic implications** — a synthesis paragraph.

Output is stored in `ResearchState.insights`.

### 5. Red team agent

Independently reviews the analysis and insights to challenge their validity:

- **Hallucination flags** — specific claims that lack evidence or appear fabricated, each with a severity level (`low`, `medium`, `high`) and a description of the issue.
- **Bias flags** — identified perspectives or framing that may skew the conclusions, each with a type and description.
- **Logical gaps** — areas where the reasoning chain has weaknesses.
- **Overall reliability** rating (`high`, `medium`, `low`).
- **Confidence adjustment** — a numeric delta applied to the Analyst's confidence score in the final report.

Output is stored in `ResearchState.red_team`.

### 6. Gap-fill agent

Reads `data_gaps` from the Analyst's output and `logical_gaps` from the Red Team's output. If any gaps are found, it constructs targeted retrieval queries and runs them through `run_tools_parallel()`. The new results are merged back into `ResearchState.retrieval_results` and stored separately in `ResearchState.gap_fill_results`.

If no gaps are identified, the agent skips retrieval and returns immediately.

### 7. Reporter agent

Assembles the complete final report from all upstream state fields:

- Applies the red team's confidence adjustment to the Analyst's score.
- Compiles the evidence table with source, title, snippet, URL, and confidence for each retrieved item.
- Structures the full output into `ResearchState.final_report`, including: title, query, executive summary, key findings, insights (trends, opportunities, risks), red team summary, evidence table, citations, and a generated-at timestamp.

---

## Retrieval Tools

| Tool | Function | Notes |
|---|---|---|
| `tool_wikipedia()` | Wikipedia article summary | Handles disambiguation errors automatically |
| `tool_arxiv()` | ArXiv paper search | Returns title, authors, abstract (up to 600 chars), URL, and publication date |
| `tool_tavily()` | Tavily web search | Returns synthesised answer + individual results; requires a Tavily API key |

All three tools return a uniform dict structure with `source`, `title`, `url`, `content`, and `query` keys, enabling the Analyst agent to process all results uniformly regardless of origin.

Tool calls are dispatched via `run_tools_parallel()`, which uses `ThreadPoolExecutor(max_workers=5)` and `as_completed()` for non-blocking concurrent execution.

---

## PDF RAG Engine

The PDF pipeline is self-contained and requires no external embedding model.

**Ingestion (at upload time):**

1. `extract_pdf_text()` — reads the PDF with PyPDF2, iterates over all pages, and splits each page's text into chunks of approximately 400 characters with a 50-character overlap stride.
2. `simple_embed()` — generates a 512-dimensional bag-of-words vector for each chunk using MD5 hashing of individual tokens. Vectors are L2-normalised.
3. `build_rag_index()` — stacks all chunk vectors and adds them to a `faiss.IndexFlatIP` (inner product) index. The index and chunk metadata are stored in `st.session_state`.

**Retrieval (at query time):**

`rag_search()` embeds the query using the same `simple_embed()` function, normalises the vector, and runs `index.search()` to return the top-k chunks by inner product score. Chunks with a score below 0.05 are filtered out.

---

## Shared State

All agents communicate through a single `ResearchState` TypedDict, which is passed through the LangGraph state machine:

| Field | Type | Description |
|---|---|---|
| `query` | `str` | The original user query |
| `sub_questions` | `List[Dict]` | Planner-generated sub-questions with priority and reasoning |
| `selected_path` | `str` | ID of the investigation path chosen by the user |
| `investigation_paths` | `List[Dict]` | All paths proposed by the Planner |
| `retrieval_results` | `List[Dict]` | Merged results from all web tools (augmented by Gap Fill) |
| `rag_results` | `List[Dict]` | Top-k PDF chunks retrieved by FAISS |
| `analysis` | `Dict` | Analyst output: summary, findings, contradictions, gaps, confidence |
| `insights` | `Dict` | Insight agent output: trends, risks, opportunities, hypotheses |
| `red_team` | `Dict` | Red Team output: hallucination flags, bias flags, reliability rating |
| `gap_fill_results` | `List[Dict]` | Additional results retrieved to fill identified gaps |
| `final_report` | `Dict` | Assembled report from the Reporter agent |
| `audit_trail` | `List[Dict]` | Timestamped log entries from all agents |
| `status` | `str` | Current pipeline status string |
| `error` | `Optional[str]` | Error message if a step failed |
| `iteration` | `int` | Iteration counter |
| `token_count` | `int` | Running estimated token usage |

---

## Installation

Clone or download `lumeris.py` and install the required packages:

```bash
pip install streamlit langgraph wikipedia arxiv requests
```

**For PDF RAG support** (optional but recommended):

```bash
pip install faiss-cpu PyPDF2 numpy
```

**For PDF export** (optional):

```bash
pip install reportlab
```

---

## Configuration

All configuration is done through the **sidebar** in the Streamlit UI at runtime. No `.env` file or config file is required.

| Setting | Required | Description |
|---|---|---|
| OpenRouter API Key | Yes | Key for LLM access via OpenRouter (`sk-or-...`) |
| Tavily API Key | No | Enables Tavily web search (`tvly-...`). Wikipedia and ArXiv work without it. |
| Model | Yes | Select from the dropdown (see [Supported Models](#supported-models)) |
| PDF upload | No | Upload a PDF to enable RAG retrieval alongside web tools |

The sidebar also displays live status indicators for each tool and the LangGraph installation.

---

## Running the App

```bash
streamlit run lumeris.py
```

The app will open at `http://localhost:8501` by default.

The app is also available at https://iznmy5gqkrbkpdnfsaq9rj.streamlit.app/

---

## Using the Interface

The UI is split into two columns: the main research panel on the left and the system status panel on the right.

**Step 1 — Configure**

Open the sidebar, enter your OpenRouter API key, optionally add a Tavily key, and select a model. Optionally upload a PDF to include as a RAG source.

**Step 2 — Plan**

Enter a research question in the text area and click **Plan Research**. The Planner agent will decompose the query into sub-questions and propose investigation paths. These are displayed immediately without running the full pipeline.

**Step 3 — Select path**

Review the sub-questions and choose an investigation path from the radio buttons. Each path shows its focus and which tools it will use.

**Step 4 — Run**

Click **Run Analysis** to execute the full agent pipeline. A progress bar and live status indicator track each stage. The right-hand panel shows the agent pipeline with colour-coded status dots (amber = running, green = complete, red = error).

**Step 5 — Review**

Once complete, the report appears in the left panel:

- Red Team warnings (if any hallucinations or bias were flagged)
- Confidence gauge with numeric score and Red Team reliability label
- Executive summary
- PDF RAG matches (if a PDF was uploaded)
- Key findings
- Tabbed insights: Trends / Opportunities / Risks
- Evidence table with source badges, titles, snippets, and confidence ratings

The right panel shows the audit trail with timestamps and per-agent log entries.

---

## Output and Exports

**In-app display** — The structured report is rendered directly in the Streamlit interface with formatted sections and a linked evidence table.

**PDF export** — If ReportLab is installed, a formatted A4 PDF is generated and available for download. The PDF includes all report sections, a styled evidence table (up to 10 rows), citations, and a header with confidence score and generation timestamp.

**JSON export** — If ReportLab is not installed (or PDF generation fails), the full report dict is exported as a pretty-printed JSON file.

---

## Token Tracking and Cost Estimation

Every LLM call returns a `usage` object from the OpenRouter API. The `total_tokens` value is accumulated in `st.session_state.token_count`. If the API does not return usage data, a fallback estimate of `len(text) / 4` tokens is used.

Estimated cost is calculated as:

```
cost = token_count * cost_per_1k_tokens / 1000
```

The cost table (`TOKEN_COST`) in the code contains blended input+output rates for all supported models. Cost and token count are displayed live in the System Status header during and after each run.

---

## Audit Trail

Every agent calls `log_step()` at the start and end of its execution, producing entries of the form:

```python
{
    "ts":      "14:32:07",       # HH:MM:SS timestamp
    "agent":   "ANALYST",        # agent name in uppercase
    "message": "Identified 2 contradictions, confidence 74%",
    "kind":    "success"         # "info" | "success" | "error"
}
```

The trail is stored on `ResearchState.audit_trail` and also mirrored to `st.session_state.audit_trail` for live display. Entries are colour-coded in the UI: success entries appear in green, error entries in red, and informational entries in the default text colour.

---

## Error Handling and Fallbacks

**Missing packages** — On startup, the app checks for all required packages and displays a clear error message with the exact `pip install` command to run if any are missing. Optional packages (FAISS, PyPDF2, ReportLab) degrade gracefully — their features are simply disabled rather than crashing the app.

**LangGraph execution** — The compiled LangGraph is tried with three invocation styles in sequence (`compiled(state)`, `compiled.run(state)`, `compiled.execute(state)`). If all fail, the pipeline falls back to sequential manual agent execution with per-step progress updates.

**Tool failures** — Each tool function wraps its logic in a try/except and returns a structured error dict (`{"source": "...", "error": "...", "query": "..."}`) rather than raising. The Retriever agent separates good results from errors, logs each error to the audit trail, and continues with whatever was successfully retrieved.

**JSON parsing** — `call_llm_json()` strips markdown code fences before parsing, and falls back to regex extraction of the first `{...}` block if `json.loads()` fails. If parsing still fails, the raw LLM response is returned with a `parse_error` flag so downstream agents can degrade gracefully.

**PDF processing** — PDF ingestion is wrapped in try/except at both the extraction and index-building stages. Failures surface as Streamlit warnings rather than crashes, and the rest of the app continues to function normally.

---

## Supported Models

The following models are available via the model selector in the sidebar. All are accessed through the OpenRouter API.

| Model | Identifier | Approx. cost / 1K tokens |
|---|---|---|
| GPT-4o Mini | `openai/gpt-4o-mini` | $0.00030 |
| GPT-4o | `openai/gpt-4o` | $0.00750 |
| Claude 3.5 Haiku | `anthropic/claude-3.5-haiku` | $0.00040 |
| Claude 3.5 Sonnet | `anthropic/claude-3.5-sonnet` | $0.00450 |
| Gemini Flash 1.5 | `google/gemini-flash-1.5` | $0.00015 |
| Mistral Nemo | `mistralai/mistral-nemo` | $0.00015 |

The default model is `openai/gpt-4o-mini`. Any model available on OpenRouter can be used by modifying the `model` selectbox options in the code.

---

## Project Structure

```
lumeris.py          # Complete application — single file
```

All logic lives in one file, structured in the following order:

```
Page config
Dependency checks and optional imports
ResearchState TypedDict definition
UI styling (custom CSS)
LLM client functions (call_llm, call_llm_json)
PDF RAG engine (extract_pdf_text, simple_embed, build_rag_index, rag_search)
Retrieval tools (tool_wikipedia, tool_arxiv, tool_tavily, run_tools_parallel)
Token estimator and cost table
Audit trail logger (log_step)
Agent functions (planner_agent, retriever_agent, analysis_agent,
                 insight_agent, red_team_agent, gap_fill_agent, report_agent)
LangGraph builder (build_graph)
Session state initialisation
UI layout (sidebar, left column, right column)
Footer
```

---

## Requirements

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | ≥ 1.32 | Web UI framework |
| `langgraph` | ≥ 0.1 | Agent orchestration state machine |
| `requests` | ≥ 2.28 | HTTP client for OpenRouter and Tavily |
| `wikipedia` | ≥ 1.4 | Wikipedia retrieval tool |
| `arxiv` | ≥ 2.0 | ArXiv search tool |
| `faiss-cpu` | ≥ 1.7 | Vector similarity search for PDF RAG *(optional)* |
| `PyPDF2` | ≥ 3.0 | PDF text extraction *(optional)* |
| `numpy` | ≥ 1.24 | Vector operations for RAG *(optional)* |
| `reportlab` | ≥ 4.0 | PDF report export *(optional)* |

Python 3.9 or later is recommended.

---

*Research Intelligence System · LangGraph + OpenRouter · Multi-Agent Orchestration*
