# Functional specification and user guide

**Product:** Local Multi-Agent Deep Researcher  
**Stack:** Python, Gradio, LangGraph, OpenRouter (LLM), FAISS (local retrieval), optional Tavily (web).

This document describes what the application does, how it is structured, and how an end user operates it from first launch to downloading a report.

---

## 1. Purpose

The application answers a **research question** by:

1. **Planning** sub-questions and search queries (LLM).
2. **Retrieving** evidence in parallel from uploaded files (PDF, images, audio), Wikipedia, arXiv, and optionally the web (Tavily).
3. **Analyzing** evidence, surfacing **contradictions**, and generating **insights** (LLM).
4. **Building** a structured **markdown report** (LLM).

Everything runs **locally** on the user’s machine; the LLM and optional Tavily calls use **networked APIs** (OpenRouter, Tavily).

---

## 2. User roles

| Role | Description |
|------|-------------|
| **Researcher (end user)** | Runs the Gradio UI, supplies question and optional files, reads the report and evidence, downloads markdown. |
| **Operator** | Installs dependencies, configures `.env`, starts `python app.py`. |

---

## 3. Functional capabilities

| ID | Capability | Notes |
|----|------------|--------|
| F-01 | Submit a natural-language research question | Required; empty submission is rejected with an error. |
| F-02 | Upload multiple files | PDFs, common image formats, and audio (e.g. mp3, wav). Audio is transcribed (Whisper-style model via Hugging Face settings). |
| F-03 | Local semantic retrieval | FAISS over ingested file content; **Top-K** is configurable in the UI (2–8, default 4). |
| F-04 | Wikipedia retrieval | Uses generated queries; no extra API key in code path described here. |
| F-05 | arXiv retrieval | Uses generated queries. |
| F-06 | Web search (Tavily) | Optional: UI checkbox **and** `TAVILY_API_KEY`. If disabled or missing, web evidence is skipped with a log message. **Web results per query** slider (1–5, default 3). |
| F-07 | Multi-agent orchestration | Fixed LangGraph pipeline (see §5); not free-form tool loops. |
| F-08 | Contradictions | Shown as a markdown list in the main column after a run. |
| F-09 | Final report | Rendered as markdown in the UI. |
| F-10 | Download report | File download; includes full detailed extracts appended after the main report when available. |
| F-11 | Detailed extracts | Toggle via **Detailed Analysis** to show or hide long retrieved snippets. |
| F-12 | Evidence catalog and trace | Collapsible **Evidence and execution trace**: table of sources and markdown trace (orchestration + retrieval log). |

---

## 4. Configuration (operator)

Settings load from **environment variables** (including a project `.env` via `python-dotenv`).

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENROUTER_API_KEY` | **Yes** | LLM access via OpenRouter. App fails at run time if missing when research starts. |
| `TAVILY_API_KEY` | No | Enables Tavily web search when the UI allows it. |
| `OPENROUTER_MODEL` | No | Default: `openai/gpt-4o-mini`. |
| `OPENROUTER_PDF_ROUTER_MODEL` | No | Optional smaller model for per-PDF retrieval phrases. |
| `EMBEDDING_MODEL` | No | Default: `sentence-transformers/all-MiniLM-L6-v2`. |
| `CHUNK_SIZE`, `CHUNK_OVERLAP` | No | Text chunking for RAG. |
| `TOP_K`, `WEB_RESULTS_PER_QUERY` | No | Defaults used if not set; UI sliders override per run for top_k and web_results_per_query. |
| `PDF_PARALLEL_WORKERS` | No | Parallelism for PDF I/O. |
| `PDF_MULTIMODAL_HF`, `PDF_SENTIMENT_HF` | No | Optional HF features (need torch/transformers). |
| `PDF_MAX_IMAGES_PER_DOCUMENT` | No | Cap on images processed per PDF. |
| `ASR_HF_MODEL`, `ASR_MAX_SECONDS` | No | Audio transcription model and max duration. |
| `GRADIO_SERVER_NAME` | No | Default `127.0.0.1`. |
| `GRADIO_SERVER_PORT` | No | Default `7860`. |

---

## 5. Internal workflow (LangGraph)

After the user clicks **Run deep research**, the graph runs in this order:

1. **planner** — Produces subquestions/queries for retrieval.  
2. **prep_retrieval** — Prepares retrieval step.  
3. **Parallel retrieval** (four branches, then merge):  
   - **local_media_retriever** — Uploaded PDFs / images / audio.  
   - **wikipedia_retriever**  
   - **arxiv_retriever**  
   - **tavily_retriever** — Skipped if web search is off or `TAVILY_API_KEY` is unset.  
4. **retriever_merge** — Single combined evidence list.  
5. **critical_analyst** — Analysis and contradiction detection.  
6. **insight_generator** — Insights / hypotheses.  
7. **report_builder** — Final markdown report and detailed extracts for the UI.

The UI **trace** and **retrieval log** reflect messages from these stages.

---

## 6. UI layout (functional map)

| Area | Element | Function |
|------|---------|----------|
| Header | Title and short description | Orientation. |
| Left column | Research question | Multi-line text input. |
| Left column | File upload | Multiple files; types include `.pdf`, images, audio extensions listed in `app.py`. |
| Left column | Enable web search | Checkbox; controls Tavily branch (still requires API key). |
| Left column | Top-K local retrieval | Slider 2–8. |
| Left column | Web results per query | Slider 1–5. |
| Left column | **Run deep research** | Starts the graph. |
| Right column | Report | Main markdown output. |
| Right column | Contradictions | Markdown list. |
| Right column | Download markdown report | File component for saved `.md`. |
| Right column | Detailed extracts + **Detailed Analysis** | Toggle visibility of long snippets. |
| Bottom (accordion) | Evidence catalog | Non-interactive dataframe: source type, label, title, URL, query, relevance hint. |
| Bottom (accordion) | Execution trace | Orchestration bullets + retrieval bullets. |

---

## 7. Outputs

- **On-screen:** Report, contradictions, optional detailed extracts, evidence table, trace.  
- **Download:** `research_report.md` (temporary directory); if detailed extracts exist, they are appended after a horizontal rule below the main report.

---

## 8. Known limits (product scope)

Aligned with `ARCHITECTURE.md`: no user accounts, no persistent multi-user database, no human-in-the-loop approvals in the graph, and citation formatting is practical markdown rather than a full academic style engine.

---

# Part B — Step-by-step user guide

## Before first use (one-time)

1. **Install Python** (3.10+ recommended; project has been used with 3.13).  
2. **Clone or open** the project folder.  
3. **Create and activate a virtual environment**, then install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Create or edit `.env`** in the project root and set **`OPENROUTER_API_KEY`**.  
5. **Optional:** set **`TAVILY_API_KEY`** if you want live web results.  
6. **Start the app:**
   ```bash
   python app.py
   ```

## Each session

1. **Open the browser** to the URL shown in the terminal (default **`http://127.0.0.1:7860`**).  
   - The app is launched with Gradio **sharing** enabled; if a public URL appears, treat it as optional and only share if you intend to expose the session.

2. **Enter your research question** in **Research question**. Be specific enough that the planner can derive useful queries (e.g. compare concepts, cite constraints, name domains).

3. **Optional — add sources:** Click **Upload PDF, image, or audio files** and select one or more files. You can run with **no uploads** (external sources only).

4. **Optional — web search:** Leave **Enable web search via Tavily** checked if you have a Tavily key and want web results; uncheck to force local + Wikipedia + arXiv only (Tavily branch skipped).

5. **Tune retrieval (optional):**  
   - **Top-K local retrieval:** more chunks from your files (higher = more context, more noise risk).  
   - **Web results per query:** only affects Tavily when enabled.

6. Click **Run deep research**. Wait until processing finishes (LLM and retrieval can take from seconds to minutes).

7. **Read the report** in the right-hand markdown panel.

8. **Review contradictions** directly under the report (if any were identified).

9. **Download:** Use **Download markdown report** to save the combined report (and detailed extracts when present).

10. **Detailed snippets:** Click **Detailed Analysis** to show full **Detailed extracts**; click again to collapse.

11. **Audit sources:** Open **Evidence and execution trace** to inspect the **Evidence catalog** table and the **Orchestration** / **Retrieval** trace.

12. **Iterate:** Adjust the question, files, or sliders and click **Run deep research** again for a new run.

---

## Troubleshooting (user-facing)

| Symptom | Likely cause |
|---------|----------------|
| Error about `OPENROUTER_API_KEY` | Key missing or empty in `.env` / environment. |
| No web results | Checkbox off, or `TAVILY_API_KEY` not set, or Tavily/API error (check trace). |
| Empty or thin report | Very broad question, no files and weak external hits, or model/output limits. |
| Slow first run | Model downloads (embeddings, Whisper, etc.) and cold start. |

For design rationale and MVP boundaries, see **`ARCHITECTURE.md`**. For install variants, see **`README.md`**.
