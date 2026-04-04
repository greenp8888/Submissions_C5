# Backend — Ideascope API

FastAPI backend with LangGraph orchestration for competitive intelligence analysis.

## Prerequisites

- Python 3.10 or higher
- **uv** (optional but recommended for faster installs) — [Install guide](https://docs.astral.sh/uv/)

## Setup

### Option A: Using uv (recommended)

```bash
cd backend

# Create virtual environment
uv venv
source .venv/bin/activate  # macOS/Linux
# or: .venv\Scripts\activate on Windows

# Install dependencies
uv pip install -r requirements.txt
```

### Option B: Using pip

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
```

### Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```
OPENROUTER_API_KEY=your_key_here
GITHUB_TOKEN=optional_but_recommended
REDDIT_CLIENT_ID=optional
REDDIT_CLIENT_SECRET=optional
PRODUCTHUNT_API_KEY=optional
```

**Required:**
- `OPENROUTER_API_KEY` — Get from https://openrouter.ai/

**Recommended:**
- `GITHUB_TOKEN` — Increases GitHub API rate limits (60 → 5000/hour)

**Optional:**
- Reddit/ProductHunt tokens — Currently using scraping fallbacks

## Run

```bash
uvicorn main:app --reload --port 8000
```

API will be available at:
- Main endpoint: `http://localhost:8000/analyze`
- Health check: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

## Architecture

### LangGraph Pipeline

```
Input → Query Builder → Parallel Retrieval → Matcher → Aggregator → Analysis → Report
```

1. **Input**: Validates idea description (max 500 chars)
2. **Query Builder**: GPT-4.1 generates 6 platform-specific search queries
3. **Parallel Retrieval**: Fetches from all sources simultaneously
4. **Matcher**: Scores items by relevance
5. **Aggregator**: Deduplicates, sorts, caps at 20 items
6. **Analysis**: GPT-4.1 generates gap analysis, features, sentiment
7. **Report Builder**: Assembles final report with traffic light indicator

### Shared Utilities

- **`utils/llm.py`**: Single OpenRouter client for all GPT-4.1 calls
- **`utils/http.py`**: Shared async HTTP client for all API requests
- **`utils/cache.py`**: 30-minute TTL cache
