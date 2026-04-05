# Setup: clone, branch, and run

Short path from zero to a running **Local Multi-Agent Deep Researcher** UI.

## 1. Clone the repository

```bash
git clone https://github.com/eng-accelerator/Submissions_C5.git
cd Submissions_C5
```

## 2. Check out the `group_12` branch

```bash
git fetch origin
git checkout group_12
```

## 3. Create the Python environment and install dependencies

```bash
cd group_12/ai-researcher
python3 -m venv .venv
source .venv/bin/activate
```

On Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Then install packages:

```bash
pip install -r requirements.txt
```

## 4. Configure API keys

From `group_12/ai-researcher` (same directory as `app.py`), copy the example env file and edit it:

```bash
cp .env.example .env
```

On Windows (PowerShell), from that same directory:

```powershell
Copy-Item .env.example .env
```

Open `.env` in an editor and set **both** of these (values come from your accounts):

| Variable | Required? | Purpose |
|----------|-----------|---------|
| `OPENROUTER_API_KEY` | **Yes** | LLM calls via [OpenRouter](https://openrouter.ai/). Paste your secret after `=`. |
| `TAVILY_API_KEY` | Recommended for web search | Live web retrieval in the UI. Leave empty only if you will turn off web search. |

Example (do not commit real keys):

```env
OPENROUTER_API_KEY=sk-or-v1-...
TAVILY_API_KEY=tvly-...
```

The other lines in `.env.example` (model names, Gradio host/port) can stay as-is unless you want to override defaults.

## 5. Start the application

```bash
python app.py
```

Open **http://127.0.0.1:7860** in a browser, or use the URL and port printed in the terminal.

---

For behavior, architecture, and UI walkthrough, see **README.md**, **ARCHITECTURE.md**, and **FUNCTIONAL.md**.
