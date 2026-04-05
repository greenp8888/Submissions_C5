# Multi-Agent AI Deep Researcher (Local-First)

A local-first, Gradio-based, LangGraph-orchestrated research assistant derived from the attached `rag_agent_colab.ipynb`.

## What it does

- Accepts a research question
- Optionally ingests multiple PDFs
- Plans an investigation
- Retrieves evidence from:
  - local PDFs
  - Tavily web search
  - arXiv
  - Wikipedia
- Critically analyzes the evidence
- Generates insights and hypotheses
- Builds a structured markdown report
- Runs locally on your machine first

## Quick start

### 1) Create and activate a virtual environment

#### Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### macOS / Linux
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Set environment variables

Copy `.env.example` to `.env` and fill in your keys.

Required:
- `OPENROUTER_API_KEY`

Optional but recommended:
- `TAVILY_API_KEY`

### 4) Run the app
```bash
python app.py
```

By default the app runs locally on:
- `http://127.0.0.1:7860`

### Streamlit UI (chat + OAuth)

```bash
streamlit run streamlitApp.py
```

Opens at `http://127.0.0.1:8501` by default.

### Docker

Build and run with Compose and `scripts/docker-deploy.sh`. Step-by-step instructions, volumes, OAuth, and registry push are in **[DOCKER.md](DOCKER.md)**. Compose files use **YAML** (`docker-compose.yml`); there is no standard `docker-compose.xml` for Docker Compose v2.

## Personal-use / local-only mode

This app is local-first by design.

- default: only your own machine can access it
- optional LAN mode: set `GRADIO_SERVER_NAME=0.0.0.0`
- optional public share: use Gradio share or a tunnel later if needed

## Suggested demo workflow

1. Start the app locally
2. Upload one or more PDFs
3. Ask a multi-hop question
4. Show the evidence table
5. Show the final report
6. Download the generated markdown report

## Notes

- If `TAVILY_API_KEY` is absent, the app still works with PDFs, Wikipedia, and arXiv.
- Uploaded PDFs are processed per run for simplicity.
- This is the right tradeoff for a hackathon MVP.

## Suggested test questions

- What are the main benefits and risks of retrieval-augmented generation for enterprise assistants?
- Based on the uploaded PDFs and current web evidence, what contradictions exist in approaches to agent evaluation?
- Compare recent trends in medical imaging AI regulation and deployment barriers.
