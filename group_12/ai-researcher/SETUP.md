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

In `group_12/ai-researcher`, create a `.env` file (same directory as `app.py`).

**Required:**

```env
OPENROUTER_API_KEY=your_key_here
```

**Optional** (web search via Tavily):

```env
TAVILY_API_KEY=your_key_here
```

## 5. Start the application

```bash
python app.py
```

Open **http://127.0.0.1:7860** in a browser, or use the URL and port printed in the terminal.

---

For behavior, architecture, and UI walkthrough, see **README.md**, **ARCHITECTURE.md**, and **FUNCTIONAL.md**.
