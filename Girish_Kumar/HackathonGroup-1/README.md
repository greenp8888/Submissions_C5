# DeepResearch — Multi-Agent AI Research Assistant

**Architecture & Execution Guide · v3**

> Orchestrates five specialised AI agents to conduct multi-hop, multi-source investigations combining concurrent web search (Tavily), local HuggingFace semantic RAG, OpenRouter LLM inference, and PDF processing to synthesise long-context research reports.

---

## Quick Stats

| Agents | Parallel searches | Report sections | Embed models | Source files |
|:------:|:-----------------:|:---------------:|:------------:|:------------:|
| 5      | 3                 | 9               | 5            | 6            |

---

## 1. Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                           User Query                                 │
│                    Topic · Context · PDFs                            │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
         ┌───────────────────▼──────────────────────────┐
         │         Agent 1 · Contextual Retriever        │
         │  ┌─────────────────────────────────────────┐  │
         │  │       ThreadPoolExecutor (parallel)      │  │
         │  │                                          │  │ ◄── Tavily API
         │  │  [Search 1] [Search 2] [Search 3]        │  │ ◄── pypdf
         │  │  [PDF 1…N ]       [HF RAG / FAISS]       │  │
         │  │                                          │  │
         │  │   Deduplicate by URL · Semantic retrieval│  │
         │  └─────────────────────────────────────────┘  │
         │         LLM synthesis → evidence digest        │
         └───────────────────┬──────────────────────────┘
                             │ evidence digest
         ┌───────────────────▼──────────────────────────┐
         │        Agent 2 · Critical Analysis            │
         │    Contradictions · credibility · gaps        │
         └───────────────────┬──────────────────────────┘
                             │ analysis report
         ┌───────────────────▼──────────────────────────┐
         │        Agent 3 · Insight Generation           │
         │    Hypotheses · trends · reasoning chains     │
         └───────────────────┬──────────────────────────┘
                             │ insights + trends
         ┌───────────────────▼──────────────────────────┐
         │            Agent 4 · Fact-Check               │
         │   Verified / unverified / disputed · score    │
         └───────────────────┬──────────────────────────┘
                             │ verified claims
         ┌───────────────────▼──────────────────────────┐
         │          Agent 5 · Report Builder             │
         │  Compiles all outputs into .md report         │
         └───────────────────┬──────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│              Final Research Report  ·  9 sections  ·  .md            │
└──────────────────────────────────────────────────────────────────────┘

   ↑ OpenRouter LLM powers all 5 agents
   ↑ Streamlit UI + .streamlit/config.toml provides the frontend
```

---

## 2. Project Gist

DeepResearch automates the full research cycle — from raw question to cited, fact-checked report — by chaining five specialised LLM agents.

**Key capabilities:**

- **Multi-hop web search** — 3 complementary sub-queries (base, recent developments, criticisms) fired concurrently via Tavily
- **Local semantic RAG** — PDFs chunked, embedded by a HuggingFace model (CPU-only, no API key), indexed in FAISS; top-k chunks retrieved per query
- **Five-agent pipeline** — each agent has a single focused system prompt; outputs chain sequentially
- **Concurrent retrieval** — ThreadPoolExecutor runs all Tavily searches + PDF extractions simultaneously; wall-clock time = max(latencies)
- **Graceful degradation** — RAG is optional; app runs without sentence-transformers/faiss-cpu using full-text PDF context
- **Native dark theme** — configured via `.streamlit/config.toml`; all sidebar widgets render correctly
- **Python 3.14 compatible** — no deprecated `__future__` imports, fully parameterised generics, no mutable defaults

---

## 3. File Structure

| File | Role | Description |
|------|------|-------------|
| `app.py` | Streamlit UI | Dark-themed frontend, sidebar controls, pipeline orchestration, live logs, report download |
| `research_engine.py` | Agent Orchestrator | `ResearchEngine` class — 5 agent methods, concurrent Tavily searches, HF RAG integration |
| `rag.py` | Local RAG Module | HuggingFace sentence-transformers + FAISS index, chunking, semantic retrieval |
| `utils.py` | Shared Helpers | `format_report_as_markdown`, `truncate`, `count_words` |
| `requirements.txt` | Dependencies | streamlit, requests, pypdf, sentence-transformers, faiss-cpu, numpy, torchvision |
| `.streamlit/config.toml` | Theme Config | Native Streamlit dark theme — primaryColor, backgroundColor, textColor |

---

## 4. The Five Agents

All agents live in `ResearchEngine` in `research_engine.py`. Data flows strictly top-down.

| # | Method | What it does |
|---|--------|-------------|
| 1 | `run_retriever()` | 3× concurrent Tavily sub-queries + parallel PDF extraction via ThreadPoolExecutor. Builds HuggingFace FAISS RAG index from PDF chunks. Deduplicates by URL. LLM synthesises evidence digest. |
| 2 | `run_analysis()` | Cross-references evidence. Identifies contradictions, rates credibility (High/Medium/Low), maps knowledge gaps, summarises consensus. |
| 3 | `run_insights()` | Generates 3–5 IF/THEN/BECAUSE hypotheses, identifies emerging trends with confidence levels, produces reasoning chains, proposes contrarian view. |
| 4 | `run_factcheck()` | Extracts 5–8 key claims. Stamps each ✅ / ⚠️ / ❌. Flags misinformation risks. Assigns reliability score: Strong / Moderate / Weak. |
| 5 | `run_report_builder()` | Compiles all four outputs into a 9-section structured markdown report. |

---

## 5. Local HuggingFace RAG

RAG pipeline when PDFs are uploaded:

1. `pypdf` extracts text (concurrent, up to 8 000 chars per PDF)
2. Text split into overlapping word-window chunks (default: 400 words, 80-word overlap)
3. Chunks embedded in batches by the chosen sentence-transformer
4. Embeddings stored in a FAISS `IndexFlatIP` (cosine similarity on normalised vectors)
5. At query time: query embedded, top-k=6 chunks retrieved, formatted as context block
6. Context block replaces raw PDF text in the Agent 1 LLM prompt

**Supported embedding models (all CPU-only):**

| Model ID | Size | Notes |
|----------|------|-------|
| `all-MiniLM-L6-v2` | ~80 MB | Default — fastest, strong general retrieval |
| `multi-qa-MiniLM-L6-cos-v1` | ~80 MB | Tuned for Q&A retrieval |
| `BAAI/bge-small-en-v1.5` | ~130 MB | Top MTEB performer at small scale |
| `BAAI/bge-base-en-v1.5` | ~440 MB | Larger BGE — highest quality |
| `all-mpnet-base-v2` | ~420 MB | Best general-purpose accuracy |

---

## 6. Final Report Structure

| # | Section | Description |
|---|---------|-------------|
| 1 | **Executive Summary** | 150–200 word overview of findings and significance |
| 2 | **Methodology** | Sources, agents used, analysis approach |
| 3 | **Key Findings** | Substantive findings with evidence citations |
| 4 | **Contradictions & Debates** | Where sources disagree and why it matters |
| 5 | **Source Credibility** | Assessment of evidence base quality |
| 6 | **Emerging Trends** | Forward-looking patterns in the evidence |
| 7 | **Hypotheses & Implications** | Testable hypotheses and strategic implications |
| 8 | **Fact-Check Summary** | Per-claim status and overall reliability score |
| 9 | **Knowledge Gaps** | What remains unknown; recommended next steps |

---

## 7. How to Execute

### Prerequisites

- Python 3.14 or later
- **OpenRouter** API key — https://openrouter.ai (prefix: `sk-or-…`)
- **Tavily** API key — https://tavily.com (prefix: `tvly-…`)
- ~80–440 MB disk space for HuggingFace model cache (first run only)

### Install & run

```bash
git clone https://github.com/your-org/deep-research-assistant.git
cd deep-research-assistant

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

streamlit run app.py               # opens http://localhost:8501
```

### Step-by-step

| Step | Action | Location | Notes |
|:----:|--------|----------|-------|
| 1 | Clone & enter dir | Terminal | |
| 2 | Create virtualenv | Terminal | |
| 3 | Install deps | `pip install -r requirements.txt` | HF models download on first RAG use |
| 4 | Launch | `streamlit run app.py` | localhost:8501 |
| 5 | API keys | Sidebar → OpenRouter + Tavily fields | Never stored to disk |
| 6 | Choose model | Sidebar → LLM Model dropdown | Default: `claude-sonnet-4.5` |
| 7 | Upload PDFs | Sidebar → Upload PDFs | Optional — enables local RAG |
| 8 | RAG settings | Sidebar → HuggingFace Local RAG | Toggle, model picker, chunk sliders |
| 9 | Query | Main text area → ▶ Investigate | Progress shown per-agent |
| 10 | Download | ⬇ Download Report (.md) | After pipeline completes |

### Available LLM models

| Model ID | Class | Best for |
|----------|-------|----------|
| `anthropic/claude-sonnet-4.5` | Sonnet | Default — balanced speed and quality |
| `anthropic/claude-sonnet-4.6` | Sonnet | Latest Sonnet, frontier performance |
| `anthropic/claude-haiku-4.5` | Haiku | Fast, cost-efficient |
| `anthropic/claude-opus-4.5` | Opus | Complex long-running research |
| `anthropic/claude-opus-4.6` | Opus | Most capable |
| `openai/gpt-4o` | GPT-4o | OpenAI alternative |
| `openai/gpt-4o-mini` | Mini | Lightweight option |

### Security notes

- API keys entered per-session — **never written to disk**
- PDF content stays local; only extracted text is sent to the LLM
- HuggingFace embedding runs 100% locally — no data leaves your machine during RAG
- All LLM calls route through OpenRouter — keys not shared with other services

---

*DeepResearch · Multi-Agent AI Research Assistant · v3*
