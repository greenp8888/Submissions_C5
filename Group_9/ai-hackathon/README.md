# AI Hackathon Deep Researcher

`ai-hackathon` is the Group 9 implementation of the Multi-Agent AI Deep Researcher described in the submission HLD. It combines a FastAPI backend, a mounted Gradio UI, LangGraph orchestration, local-first document retrieval, public-provider enrichment, transparent credibility scoring, and humanized export into a single runnable app.

## What This Project Does

The application accepts a research question, optional multi-topic batch input, and optional uploaded files. It creates a local knowledge collection, searches that local corpus first, then enriches with public sources when needed. It produces:

- a structured long-form research report
- confidence and trust signals with credibility rationale
- contradiction summaries
- follow-up questions
- graph-ready entities and relationships
- an agent trace of major orchestration steps
- a formatted PDF export with readable narrative structure

The app is designed to keep working even when external API keys are missing or invalid by falling back to local-only and heuristic behavior.

## Core Features

- FastAPI backend with research, report, graph, trace, export, and knowledge endpoints
- provider settings API for OpenRouter and Tavily
- Gradio UI mounted at the app root
- LangGraph pipeline with planner -> retrieval -> analysis -> insights -> report
- Local-first retrieval with PDF/TXT/Markdown ingestion
- source toggles for Local RAG, Web/Tavily, and arXiv
- date-range inputs with quick presets for external research windows
- single-question and user-entered batch research modes
- Public-provider clients for OpenRouter, Tavily, and arXiv
- Secondary adapter placeholders for Semantic Scholar, PubMed, NewsAPI, and GDELT
- SSE-style progress event model stored in-memory
- Dig-deeper flow from findings, claims, and insights
- comprehensive references with local filenames and PDF page numbers where available
- Markdown and humanized PDF export

## Architecture Summary

### Main flow

1. User submits a question and optional files.
2. Files are parsed, chunked, embedded, and stored in a local collection.
3. Planner decomposes the query into sub-questions.
4. Local retrieval runs first for each sub-question.
5. Public retrieval runs only when local evidence is not enough and only from the user-enabled source channels.
6. External retrieval respects the requested date range or quick preset where provider metadata allows.
7. Analysis converts findings into claims, contradictions, and trust/confidence signals.
8. Credibility scoring explains why each source was trusted or discounted.
9. Report builder creates the final structured report and export-ready narrative.
10. Insight generation builds follow-up questions, entities, and relationships.

### Local-first behavior

- If local collections exist, the app searches them first.
- If uploaded PDFs exist but indexing is incomplete, PDF fallback retrieval is used before public retrieval.
- Citations prefer local evidence before external evidence.
- Public retrieval is enrichment, not the first step.
- PDF-based RAG citations preserve the original filename and page number in both report output and the reference appendix.

## Project Structure

```text
ai-hackathon/
|-- pyproject.toml
|-- README.md
|-- .env.example
|-- start.ps1
|-- stop.ps1
|-- start.bat
|-- stop.bat
|-- prompts/
|-- src/
|   `-- ai_app/
|       |-- agents/
|       |-- api/
|       |-- domain/
|       |-- llms/
|       |-- memory/
|       |-- orchestration/
|       |-- retrieval/
|       |-- schemas/
|       `-- services/
`-- ui/
    |-- components/
    |-- gradio/
    `-- services/
```

## Requirements

- Windows PowerShell environment for the provided scripts
- Python 3.10 or newer
- Internet access if using OpenRouter, Tavily, or arXiv live

Optional API credentials:

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `TAVILY_API_KEY`

Optional app settings:

- `AI_HACKATHON_DATA_DIR`
- `AI_HACKATHON_TOP_K`
- `AI_HACKATHON_EMBED_DIM`
- `AI_HACKATHON_DEBUG`

## Quick Start

### First-time setup

```powershell
cd E:\hackathon-project\Submissions_C5\Group_9\ai-hackathon
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
Copy-Item .env.example .env
```

Add keys to `.env` only if you want live provider behavior. The app can still run without them.

### Start the app

```powershell
.\start.ps1
```

By default this starts:

- host: `127.0.0.1`
- port: `8000`
- UI: `http://127.0.0.1:8000/`
- health: `http://127.0.0.1:8000/health`

### Stop the app

```powershell
.\stop.ps1
```

## Start/Stop Scripts

### `start.ps1`

Responsibilities:

- chooses `.venv\Scripts\python.exe` when present, otherwise falls back to `python`
- creates `.runtime\`
- starts `uvicorn ai_app.main:app`
- writes the PID to `.runtime\server.pid`
- writes stdout/stderr logs to `.runtime\server.out.log` and `.runtime\server.err.log`
- prevents duplicate starts when the server is already running

Useful examples:

```powershell
.\start.ps1
.\start.ps1 -Port 8010
.\start.ps1 -BindHost 0.0.0.0 -Port 8000 -Reload
```

### `stop.ps1`

Responsibilities:

- reads `.runtime\server.pid`
- stops the background process if it still exists
- removes stale PID files when needed

### Batch wrappers

- `start.bat`
- `stop.bat`

These simply call the PowerShell scripts and are useful when launching from Explorer or `cmd`.

## Running Without Scripts

You can still run the app manually:

```powershell
cd E:\hackathon-project\Submissions_C5\Group_9\ai-hackathon
python -m uvicorn ai_app.main:app --app-dir src --host 127.0.0.1 --port 8000
```

## Environment Configuration

Create a local `.env` file in the app root.

Example:

```env
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-4o-mini
TAVILY_API_KEY=
AI_HACKATHON_DATA_DIR=.data
AI_HACKATHON_TOP_K=5
AI_HACKATHON_EMBED_DIM=64
```

Notes:

- if `OPENROUTER_API_KEY` is empty, planning and analysis use fallback heuristics
- if `TAVILY_API_KEY` is empty, web/news retrieval is skipped gracefully
- arXiv can run without an API key

## Main Endpoints

### Health

- `GET /health`

### Research

- `POST /api/research`
- `GET /api/research/{id}/stream`
- `GET /api/research/{id}/state`
- `GET /api/research/{id}/report`
- `GET /api/research/{id}/graph`
- `GET /api/research/{id}/trace`
- `POST /api/research/{id}/dig-deeper`
- `GET /api/research/{id}/export/markdown`
- `GET /api/research/{id}/export/pdf`

### Settings

- `GET /api/settings/providers`
- `POST /api/settings/providers`

### Knowledge

- `POST /api/knowledge/upload`
- `GET /api/knowledge/collections`
- `GET /api/knowledge/collections/{id}`

## Typical Usage

### From the UI

1. Open the app root URL in the browser.
2. Configure OpenRouter and Tavily keys from the provider settings panel if you want live LLM or web retrieval.
3. Enter a research question, or switch to batch mode and enter one topic per line.
4. Choose which sources to use: Local RAG, Web/Tavily, and/or arXiv.
5. Apply a quick date preset or set an explicit `start_date` and `end_date`.
6. Select `quick`, `standard`, or `deep`.
7. Upload local files if you want local-first evidence, and optionally refresh collections to reuse an indexed set.
8. Start research.
9. Inspect the progress timeline, long-form report, references, confidence table, graph, and trace tabs.
10. Use Dig Deeper with a finding, claim, or insight target when needed.
11. Export markdown or PDF from the UI.

### From the API

Minimal JSON request:

```json
{
  "query": "What are the most promising approaches to treating Alzheimer's?",
  "depth": "standard",
  "collection_ids": [],
  "use_local_corpus": true,
  "enabled_sources": ["local_rag", "web", "arxiv"],
  "date_preset": "last_1_year",
  "start_date": "2025-04-04",
  "end_date": "2026-04-04",
  "run_mode": "single",
  "batch_topics": []
}
```

## Local Data and Runtime Files

### `.data/`

Stores:

- indexed local collections
- chunk metadata
- exported markdown and PDF files

### `.runtime/`

Created by `start.ps1`. Stores:

- `server.pid`
- `server.out.log`
- `server.err.log`

## Validation Already Performed

The current implementation has been validated with:

- `python -m compileall Group_9\ai-hackathon\src Group_9\ai-hackathon\ui`
- editable install via `pip install -e Group_9\ai-hackathon`
- app import smoke test
- fallback research run without provider keys
- local-first ingestion and retrieval smoke test
- PDF ingestion smoke test confirming filename and page-number carry-through
- provider-settings API route presence smoke test
- humanized PDF export smoke test
- batch-mode and quick-date-preset contract smoke test

## Known Limits

- Semantic Scholar, PubMed, NewsAPI, and GDELT are adapter stubs in this pass
- Graph rendering currently uses a simple HTML/JSON fallback rather than a rich interactive visualization
- Confidence and analysis logic are heuristic when LLM credentials are not configured
- Session state is in-memory only
- There is no persistent database in this MVP
- Some web results may not expose reliable publication dates, so date filtering is strongest for arXiv and weaker for generic web results

## Troubleshooting

### Server does not start

- make sure dependencies are installed with `pip install -e .`
- check `.runtime\server.err.log`
- check whether another app is already using the port

### `start.ps1` says the server is already running

- run `.\stop.ps1`
- if needed, delete `.runtime\server.pid` after confirming the process is gone

### UI loads but external results are sparse

- this is expected when API keys are not configured
- local uploads and arXiv can still provide useful output

### Imports fail

- activate `.venv` if you created one
- reinstall with `pip install -e .`

## Next Recommended Improvements

- add automated API and integration tests
- improve graph visualization
- add richer structured LLM outputs for claims and insights
- enable the secondary provider adapters
- improve source ranking and contradiction quality with real evaluation loops
