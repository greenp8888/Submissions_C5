# DeepResearch — Multi-Agent AI Research Assistant

**Architecture Reference & Execution Guide** · v2 (Concurrent Retrieval)

> A Streamlit application that orchestrates multi-hop, multi-source research
> investigations and synthesises long-context reports via OpenRouter LLMs and
> Tavily web search. Agent 1 now fires all searches and PDF extractions
> simultaneously using `concurrent.futures.ThreadPoolExecutor`.

---

## Quick Stats

| Agents | Report Sections | Dependencies | API Keys | Max Worker Threads |
|:------:|:---------------:|:------------:|:--------:|:------------------:|
| 5      | 9               | 3            | 2        | 10                 |

---

## 1. Architecture Overview

Agents 2–5 run **sequentially** — each depends on the output of the previous
one. Inside **Agent 1**, all Tavily sub-queries and all PDF extractions run
**concurrently** inside a single `ThreadPoolExecutor`.

```
┌──────────────────────────────────────────────────────────┐
│                      User Query                          │
│               Topic · Context · PDFs                     │
└────────────────────────┬─────────────────────────────────┘
                         │
         ┌───────────────▼───────────────┐
         │     Agent 1 · Contextual      │
         │         Retriever             │
         │  ┌────────────────────────┐   │
         │  │  ThreadPoolExecutor    │   │
         │  │  (all tasks parallel)  │   │
         │  │                        │   │
         │  │  ┌──────┐ ┌──────┐    │   │ ◄── Tavily: base query
         │  │  │Search│ │Search│    │   │ ◄── Tavily: recent devs
         │  │  │  1   │ │  2   │    │   │ ◄── Tavily: criticism angle
         │  │  └──────┘ └──────┘    │   │
         │  │  ┌──────┐ ┌──────┐    │   │ ◄── PDF 1 (pypdf)
         │  │  │Search│ │ PDF  │    │   │ ◄── PDF 2 (pypdf)
         │  │  │  3   │ │  ...  │   │   │ ◄── PDF N (pypdf)
         │  │  └──────┘ └──────┘    │   │
         │  │   Deduplicate by URL   │   │
         │  └────────────────────────┘   │
         │     LLM synthesis → digest    │
         └───────────────┬───────────────┘
                         │ evidence digest
         ┌───────────────▼───────────────┐
         │   Agent 2 · Critical Analysis │
         │  Contradictions · credibility │
         └───────────────┬───────────────┘
                         │ analysis report
         ┌───────────────▼───────────────┐
         │  Agent 3 · Insight Generation │
         │  Hypotheses · trends · chains │
         └───────────────┬───────────────┘
                         │ insights + trends
         ┌───────────────▼───────────────┐
         │     Agent 4 · Fact-Check      │
         │  ✓ / ? / ✗ · reliability     │
         └───────────────┬───────────────┘
                         │ verified claims
         ┌───────────────▼───────────────┐
         │    Agent 5 · Report Builder   │
         │  Compiles all into .md report │
         └───────────────┬───────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│               Final Research Report                      │
│           9 sections · downloadable .md                  │
└──────────────────────────────────────────────────────────┘

        ↑ OpenRouter LLM powers all 5 agents
```

---

## 2. Concurrency Model (Agent 1)

### 2.1 Before vs After

| | Before (serial) | After (concurrent) |
|---|---|---|
| Searches fired | 1 query | 3 sub-queries |
| PDFs extracted | Serial `for` loop | Parallel futures |
| Total wait | `sum(all latencies)` | `max(all latencies)` |
| Partial failure | One error stops all | Failed futures log a placeholder; others succeed |
| Deduplication | N/A | By URL — highest-score copy kept |

### 2.2 Sub-query decomposition

`_build_sub_queries()` expands the single user query into three complementary
angles fired simultaneously — no extra LLM call required:

| # | Angle | Purpose |
|---|-------|---------|
| 1 | Base query (+ extra context) | Core topic coverage |
| 2 | `"... latest research recent developments 2024 2025"` | Recency bias correction |
| 3 | `"... challenges limitations criticism controversies"` | Counter-evidence discovery |

### 2.3 Thread pool design

```python
_MAX_WORKERS = 10   # shared budget for searches + PDF tasks

with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
    search_futures = {pool.submit(_tavily_search, q, key, n): q for q in sub_queries}
    pdf_futures    = {pool.submit(_extract_pdf_text, pdf): pdf for pdf in pdf_files}

    for future in as_completed(search_futures):   # collect as they land
        ...
    for future in as_completed(pdf_futures):
        ...
```

A **single executor** handles both search and PDF tasks so the thread budget
is shared and no second pool is opened back-to-back.

---

## 3. Module Descriptions

### 3.1 `app.py` — Streamlit UI

Entry point. Renders the dark-themed interface, sidebar controls, live
progress bar, per-agent activity log, metric cards, and the final downloadable
report.

**Sidebar controls:**
- OpenRouter API key (password masked)
- Tavily API key (password masked)
- LLM model selector
- Max web search results slider (3–15)
- Max tokens per agent slider (512–4096)
- PDF file uploader (multiple files)

**Live feedback during pipeline:**
- Progress bar advancing 10 → 30 → 55 → 75 → 88 → 100 %
- Colour-coded agent log: teal = retriever · blue = analysis · purple = insight · green = report · red = error

**Output:**
- Metric cards: sources · contradictions · hypotheses · verified claims
- Rendered markdown report
- `⬇ Download Report (.md)` button

---

### 3.2 `research_engine.py` — Agent Orchestrator

Contains the `ResearchEngine` class plus all module-level helpers.

#### Module-level helpers

| Function | Returns | Purpose |
|----------|---------|---------|
| `_llm()` | `str` | POST to OpenRouter, return assistant text |
| `_tavily_search()` | `list[dict]` | Single Tavily search; prepends synthesised answer |
| `_tavily_search_concurrent()` | `list[dict]` | Standalone helper — fires a custom query list in parallel |
| `_build_sub_queries()` | `list[str]` | Expands one query into 3 complementary angles |
| `_extract_pdf_text()` | `str` | Extract up to 8 000 chars from one PDF via pypdf |
| `_extract_pdfs_concurrent()` | `list[str]` | Standalone helper — extracts all PDFs in parallel |
| `_count_re()` | `int` | Regex match counter used for metrics |

#### Agent methods

| # | Method | Input | Output | Key actions |
|---|--------|-------|--------|-------------|
| 1 | `run_retriever()` | Query, PDFs | Evidence digest | 3× concurrent Tavily searches + parallel PDF extraction, dedup by URL, LLM synthesis |
| 2 | `run_analysis()` | Evidence digest | Analysis report | Contradiction detection, source credibility rating, gap mapping |
| 3 | `run_insights()` | Digest + analysis | Insights + trends | IF/THEN hypotheses, trend identification, reasoning chains |
| 4 | `run_factcheck()` | Analysis + insights | Verified claims | Per-claim ✅/⚠️/❌ status, reliability score |
| 5 | `run_report_builder()` | All above outputs | Final .md report | 9-section structured report |

**Python 3.14 compatibility:**
- No `from __future__ import annotations` (PEP 563 withdrawn; PEP 649 is 3.14 default)
- Fully parameterised generics: `list[dict[str, Any]]`, `dict[str, Any]`
- `X | Y` union syntax (valid since 3.10, no shim needed)
- No mutable default arguments

---

### 3.3 `utils.py` — Shared Helpers

| Function | Signature | Purpose |
|----------|-----------|---------|
| `format_report_as_markdown()` | `(text: str) -> str` | Strips LLM triple-backtick fences |
| `truncate()` | `(text: str, max_chars: int = 500) -> str` | Word-boundary truncation |
| `count_words()` | `(text: str) -> int` | Whitespace-split word counter |

---

### 3.4 `requirements.txt` — Dependencies

```text
# Python >= 3.14 required
streamlit>=1.40.0   # Web UI framework
requests>=2.32.0    # HTTP calls to OpenRouter & Tavily
pypdf>=5.1.0        # PDF text extraction for RAG
```

`concurrent.futures` is stdlib — no extra install needed.

---

## 4. Final Report Structure (9 Sections)

| # | Section | Description |
|---|---------|-------------|
| 1 | **Executive Summary** | 150–200 word overview of findings and significance |
| 2 | **Methodology** | Sources consulted, agents used, analysis approach |
| 3 | **Key Findings** | Substantive findings with evidence citations |
| 4 | **Contradictions & Debates** | Where sources disagree and why it matters |
| 5 | **Source Credibility Analysis** | Assessment of evidence base quality |
| 6 | **Emerging Trends** | Forward-looking patterns in the evidence |
| 7 | **Hypotheses & Implications** | Testable hypotheses and strategic implications |
| 8 | **Fact-Check Summary** | Key claims, verification status, reliability score |
| 9 | **Knowledge Gaps & Future Research** | What remains unknown; next steps |

---

## 5. How to Execute the Project

### 5.1 Prerequisites

- Python 3.14 or later
- **OpenRouter** account and API key — https://openrouter.ai
- **Tavily** account and API key — https://tavily.com
- Internet access for both APIs

### 5.2 Step-by-step

| Step | Action | Command / Location | Notes |
|:----:|--------|--------------------|-------|
| 1 | Clone project | `git clone <repo-url> && cd deep-research-assistant` | |
| 2 | Create virtualenv | `python -m venv .venv && source .venv/bin/activate` | Windows: `.venv\Scripts\activate` |
| 3 | Install deps | `pip install -r requirements.txt` | streamlit, requests, pypdf |
| 4 | Launch app | `streamlit run app.py` | Opens http://localhost:8501 |
| 5 | Enter OpenRouter key | Sidebar → OpenRouter API Key | Prefix: `sk-or-…` |
| 6 | Enter Tavily key | Sidebar → Tavily API Key | Prefix: `tvly-…` |
| 7 | Choose model | Sidebar → LLM Model dropdown | Default: `claude-sonnet-4.5` |
| 8 | Upload PDFs (optional) | Sidebar → Upload PDFs | Any number of `.pdf` files |
| 9 | Type research query | Main text area | Be specific for best results |
| 10 | Click Investigate | `▶ Investigate` button | Pipeline runs; progress shown |
| 11 | Download report | `⬇ Download Report (.md)` | Appears after completion |

### 5.3 Full install + run commands

```bash
# 1. Clone
git clone https://github.com/your-org/deep-research-assistant.git
cd deep-research-assistant

# 2. Virtualenv (recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install
pip install -r requirements.txt

# 4. Run
streamlit run app.py
```

### 5.4 Environment variable alternative

```bash
export OPENROUTER_API_KEY='sk-or-...'
export TAVILY_API_KEY='tvly-...'
```

Read as defaults in `app.py`:

```python
import os
openrouter_key = st.text_input("OpenRouter API Key", type="password",
                                value=os.getenv("OPENROUTER_API_KEY", ""))
tavily_key     = st.text_input("Tavily API Key",     type="password",
                                value=os.getenv("TAVILY_API_KEY", ""))
```

### 5.5 Available models (via OpenRouter)

| Model ID | Class | Best for |
|----------|-------|----------|
| `anthropic/claude-sonnet-4.5` | Sonnet | Default — balanced speed and quality |
| `anthropic/claude-sonnet-4.6` | Sonnet | Latest Sonnet, frontier performance |
| `anthropic/claude-haiku-4.5` | Haiku | Fast, cost-efficient queries |
| `anthropic/claude-opus-4.5` | Opus | Complex, long-running research |
| `anthropic/claude-opus-4.6` | Opus | Most capable for deep analysis |
| `openai/gpt-4o` | GPT-4o | OpenAI alternative |
| `openai/gpt-4o-mini` | GPT-4o Mini | Lightweight OpenAI option |
| `google/gemini-pro-1.5` | Gemini | Google alternative |
| `meta-llama/llama-3.1-70b-instruct` | Llama | Open-source option |

---

## 6. Project File Structure

```
deep-research-assistant/
├── app.py                  # Streamlit UI — entry point
├── research_engine.py      # Five-agent orchestrator (concurrent retrieval)
├── utils.py                # Shared helper functions
├── requirements.txt        # Python dependencies
└── README.md               # Setup instructions
```

---

## 7. Security Notes

- API keys are entered per-session and **never written to disk** by default.
- Do not commit keys to version control — use `.env` files or env vars.
- PDF content stays local; only extracted text is sent to the LLM.
- All LLM calls route through OpenRouter — keys are not shared elsewhere.
- Add `.env` to `.gitignore` if using a local environment file.

---

## 8. Extending the System

### Add a new agent

1. Add a `run_<name>()` method to `ResearchEngine` in `research_engine.py`
2. Insert the call in `app.py` between relevant existing steps
3. Redistribute progress bar percentages across the new total
4. Add a log entry with the appropriate `kind` class for colour coding

```python
# Example: adding a "Gap Analysis" agent after fact-check
gap_result = engine.run_gap_analysis(query, analysis_result, factcheck_result)
add_log(f"Identified {gap_result['gap_count']} research gaps.", "insight")
progress_bar.progress(82)
```

### Increase search parallelism

Raise `_MAX_WORKERS` in `research_engine.py` (default 10) or add more
sub-query angles in `_build_sub_queries()`:

```python
def _build_sub_queries(query: str, extra_context: str) -> list[str]:
    base = f"{query}. {extra_context[:200]}" if extra_context else query
    return [
        base,
        f"{query} latest research recent developments 2024 2025",
        f"{query} challenges limitations criticism controversies",
        f"{query} statistics data market size",       # ← add more angles
        f"{query} case studies real world examples",  # ← here
    ]
```

---

*DeepResearch · Multi-Agent AI Research Assistant · v2 (Concurrent Retrieval)*
