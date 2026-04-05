# DeepResearch — Multi-Agent AI Research Assistant

**Architecture Reference & Execution Guide**

> A Streamlit application that orchestrates multi-hop, multi-source research investigations and synthesises long-context reports via OpenRouter LLMs and Tavily web search.

---

## Quick Stats

| Agents | Report Sections | Dependencies | API Keys Required |
|:------:|:---------------:|:------------:|:-----------------:|
| 5      | 9               | 3            | 2                 |

---

## 1. Architecture Overview

The pipeline runs sequentially — each agent passes its structured output to the next. All five agents call the OpenRouter LLM endpoint; only Agent 1 makes external API calls (Tavily and pypdf).

```
┌─────────────────────────────────────────┐
│             User Query                  │
│       Topic · Context · PDFs            │
└──────────────────┬──────────────────────┘
                   │
         ┌─────────▼──────────┐   ◄── Tavily API
         │                    │   ◄── PDF (pypdf)
         │  Agent 1           │
         │  Contextual        │
         │  Retriever         │
         │                    │
         └─────────┬──────────┘
                   │ evidence digest
         ┌─────────▼──────────┐
         │  Agent 2           │
         │  Critical          │
         │  Analysis          │
         └─────────┬──────────┘
                   │ analysis report
         ┌─────────▼──────────┐
         │  Agent 3           │
         │  Insight           │
         │  Generation        │
         └─────────┬──────────┘
                   │ insights + trends
         ┌─────────▼──────────┐
         │  Agent 4           │
         │  Fact-Check        │
         └─────────┬──────────┘
                   │ verified claims
         ┌─────────▼──────────┐
         │  Agent 5           │
         │  Report Builder    │
         └─────────┬──────────┘
                   │
┌──────────────────▼──────────────────────┐
│         Final Research Report           │
│      9 sections · downloadable .md      │
└─────────────────────────────────────────┘

        ↑ OpenRouter LLM powers all agents
```

---

## 2. Module Descriptions

### 2.1 `app.py` — Streamlit UI

The entry point of the application. Renders the dark-themed web interface using custom CSS injected via `st.markdown`. Provides the sidebar for API key input, model selection, and PDF uploads. Orchestrates the five-agent pipeline by calling `ResearchEngine` methods in sequence, updating a progress bar and per-agent activity log after each step. Renders the final report and exposes a download button for the `.md` file.

**Sidebar controls:**
- OpenRouter API key input (password masked)
- Tavily API key input (password masked)
- LLM model selector dropdown
- Max web search results slider (3–15)
- Max tokens per agent slider (512–4096)
- PDF file uploader (multiple files, RAG context)

**Main area:**
- Research query text area
- Optional extra-context expander
- `▶ Investigate` button

**Live feedback:**
- Colour-coded agent activity log: teal = retriever, blue = analysis, purple = insight, green = report, red = error
- Progress bar advancing through each agent step

**Output:**
- Metric cards: sources consulted · contradictions found · hypotheses generated · claims verified
- Rendered markdown report
- `⬇ Download Report (.md)` button

---

### 2.2 `research_engine.py` — Agent Orchestrator

Contains the `ResearchEngine` class that wraps all five agents as methods. Each method constructs a focused system prompt + user prompt and calls `_llm()`, a thin wrapper around the OpenRouter `/v1/chat/completions` endpoint.

**Python 3.14 compatibility notes:**
- No `from __future__ import annotations` (PEP 563 withdrawn; PEP 649 is the 3.14 default)
- Fully parameterised generics: `list[dict[str, Any]]`, `dict[str, Any]`
- `X | Y` union syntax used directly (valid since 3.10)
- No mutable default arguments (`pdf_files: list[Any] | None = None`)

#### Agent Methods

| # | Method | Input | Output | Key Actions |
|---|--------|-------|--------|-------------|
| 1 | `run_retriever()` | Query, PDFs | Evidence digest | Tavily web search, pypdf text extraction, LLM synthesis |
| 2 | `run_analysis()` | Evidence digest | Analysis report | Contradiction detection, source credibility rating, gap mapping |
| 3 | `run_insights()` | Digest + analysis | Insights + trends | IF/THEN hypotheses, trend identification, reasoning chains |
| 4 | `run_factcheck()` | Analysis + insights | Verified claims | Per-claim ✅/⚠️/❌ status, reliability score (Strong/Moderate/Weak) |
| 5 | `run_report_builder()` | All above outputs | Final .md report | 9-section structured report, downloadable markdown file |

#### Module-level helpers

| Function | Signature | Purpose |
|----------|-----------|---------|
| `_llm()` | `(messages, openrouter_key, model, max_tokens, system) -> str` | POST to OpenRouter, return assistant text |
| `_tavily_search()` | `(query, tavily_key, max_results) -> list[dict[str, Any]]` | Search Tavily, prepend synthesised answer |
| `_extract_pdf_text()` | `(file_obj) -> str` | Extract up to 8 000 chars from a PDF via pypdf |
| `_count_re()` | `(pattern, text) -> int` | Regex match count helper for metrics |

---

### 2.3 `utils.py` — Shared Helpers

Three lightweight utility functions:

| Function | Signature | Purpose |
|----------|-----------|---------|
| `format_report_as_markdown()` | `(text: str) -> str` | Strips LLM-inserted triple-backtick fences |
| `truncate()` | `(text: str, max_chars: int = 500) -> str` | Word-boundary truncation for context-window safety |
| `count_words()` | `(text: str) -> int` | Simple whitespace-split word counter |

---

### 2.4 `requirements.txt` — Dependencies

```text
# Python >= 3.14 required
streamlit>=1.40.0   # Web UI framework
requests>=2.32.0    # HTTP calls to OpenRouter & Tavily
pypdf>=5.1.0        # PDF text extraction for RAG
```

---

## 3. Final Report Structure

The Report Builder Agent (Agent 5) compiles all previous agent outputs into a 9-section structured markdown document.

| # | Section | Description |
|---|---------|-------------|
| 1 | **Executive Summary** | 150–200 word overview of findings and significance |
| 2 | **Methodology** | Sources consulted, agents used, analysis approach |
| 3 | **Key Findings** | Substantive findings with evidence citations |
| 4 | **Contradictions & Debates** | Where sources disagree and why it matters |
| 5 | **Source Credibility Analysis** | Assessment of evidence base quality |
| 6 | **Emerging Trends** | Forward-looking patterns identified in the evidence |
| 7 | **Hypotheses & Implications** | Testable hypotheses and strategic implications |
| 8 | **Fact-Check Summary** | Key claims, verification status, reliability score |
| 9 | **Knowledge Gaps & Future Research** | What remains unknown; next investigative steps |

---

## 4. How to Execute the Project

### 4.1 Prerequisites

- Python 3.14 or later
- An **OpenRouter** account and API key — https://openrouter.ai
- A **Tavily** account and API key — https://tavily.com
- Internet access for both APIs

---

### 4.2 Step-by-Step Execution

| Step | Action | Command / Location | Notes |
|:----:|--------|--------------------|-------|
| 1 | Install dependencies | `pip install -r requirements.txt` | streamlit, requests, pypdf |
| 2 | Launch the app | `streamlit run app.py` | Opens http://localhost:8501 |
| 3 | Enter OpenRouter key | Sidebar → OpenRouter API Key | Prefix: `sk-or-…` |
| 4 | Enter Tavily key | Sidebar → Tavily API Key | Prefix: `tvly-…` |
| 5 | Choose model | Sidebar → LLM Model dropdown | Default: `claude-sonnet-4.5` |
| 6 | Upload PDFs (optional) | Sidebar → Upload PDFs | Any number of `.pdf` files |
| 7 | Type research query | Main text area | Be specific for best results |
| 8 | Click Investigate | `▶ Investigate` button | Pipeline runs; progress shown |
| 9 | Download report | `⬇ Download Report (.md)` button | Appears after completion |

---

### 4.3 Full Install & Run Commands

```bash
# 1. Clone or download the project
git clone https://github.com/your-org/deep-research-assistant.git
cd deep-research-assistant

# 2. (Optional) create a virtual environment
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch Streamlit
streamlit run app.py
```

---

### 4.4 Environment Variable Alternative

Instead of entering API keys in the UI on every session, export them as environment variables:

```bash
export OPENROUTER_API_KEY='sk-or-...'
export TAVILY_API_KEY='tvly-...'
```

Then read them in `app.py` as fallback defaults:

```python
import os
openrouter_key = st.text_input("OpenRouter API Key", type="password",
                                value=os.getenv("OPENROUTER_API_KEY", ""))
tavily_key     = st.text_input("Tavily API Key",     type="password",
                                value=os.getenv("TAVILY_API_KEY", ""))
```

---

### 4.5 Available Models (via OpenRouter)

| Model ID | Class | Best For |
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

## 5. Security Notes

- API keys are entered per-session and **never written to disk** by default.
- Do not commit keys to version control — use `.env` files or environment variables.
- PDF content stays local; only extracted text is sent to the LLM.
- All LLM calls route through OpenRouter — your keys are not shared with other services.
- Add `.env` to your `.gitignore` if using a local environment file.

---

## 6. Project File Structure

```
deep-research-assistant/
├── app.py                  # Streamlit UI — entry point
├── research_engine.py      # Five-agent orchestrator
├── utils.py                # Shared helper functions
├── requirements.txt        # Python dependencies
└── README.md               # Setup instructions
```

---

## 7. Extending the System

To add a new agent:

1. Add a `run_<agent_name>()` method to `ResearchEngine` in `research_engine.py`
2. Insert the agent call in `app.py` between the relevant existing steps
3. Update the progress bar percentages to redistribute across the new total
4. Add a new log entry with an appropriate `kind` class for colour coding

```python
# Example: adding a "Gap Analysis" agent after fact-check
gap_result = engine.run_gap_analysis(query, analysis_result, factcheck_result)
add_log(f"Identified {gap_result['gap_count']} research gaps.", "insight")
progress_bar.progress(82)
```

---

*DeepResearch · Multi-Agent AI Research Assistant*
