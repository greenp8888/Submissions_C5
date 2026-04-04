# Ideascope — Setup & Run Guide

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **uv** (recommended for faster installs) — [Install guide](https://docs.astral.sh/uv/)

## Quick Start

### Backend

**Option A: Using uv (recommended — faster)**

```bash
cd backend

# Create virtual environment
uv venv
source .venv/bin/activate  # macOS/Linux
# or: .venv\Scripts\activate on Windows

# Install dependencies
uv pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Run server
uvicorn main:app --reload --port 8000
```

**Option B: Using pip (standard)**

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Run server
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000`

## Environment Variables

### Backend `.env`

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
- `GITHUB_TOKEN` — Increases rate limits from 60 to 5000/hour

### Frontend `.env.local` (optional)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Architecture

- Frontend (Next.js) → `http://localhost:3000`
- Backend (FastAPI) → `http://localhost:8000`
- LLM: OpenRouter API with GPT-4.1

The backend uses LangGraph to orchestrate 6 parallel retrieval agents (GitHub, Reddit, HN, Product Hunt, AI For That, YC), then analyzes results with GPT-4.1 and streams the report back via Server-Sent Events.

## Testing

Once both servers are running:

1. Open `http://localhost:3000`
2. Enter a product idea (e.g., "AI-powered email summarizer for executives")
3. Click "Analyze idea →"
4. Watch the streaming progress as results come in

## Troubleshooting

**Backend won't start:**
- Make sure virtual environment is activated
- Check that `.env` file exists with `OPENROUTER_API_KEY`
- Verify you're in the `backend/` directory

**Frontend can't connect:**
- Ensure backend is running on port 8000
- Check CORS settings in `backend/main.py`
- Try accessing `http://localhost:8000/health`

**Import errors:**
- The `sys.path.insert()` in `main.py` handles module resolution
- Make sure you're running from the `backend/` directory
