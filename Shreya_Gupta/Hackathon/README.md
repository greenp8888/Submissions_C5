# 🔬 Autonomous Multi-Agent Research Assistant

> **Agentic RAG pipeline** built with LangGraph · LangChain · ChromaDB · ArXiv · Tavily · Streamlit  
> Hackathon Project — AI Accelerator C5 | Author: Shreya Gupta (d_u_u_u_h_h)


Which Assignment this is?
4. Multi-Agent AI Deep Researcher
What it demonstrates:
An AI-powered research assistant for multi-hop, multi-source investigations. The system spins up specialized agents that:
Contextual Retriever Agent – Pulls data from research papers, news articles, reports, and APIs.
Critical Analysis Agent – Summarizes findings, highlights contradictions, and validates sources.
Insight Generation Agent – Suggests hypotheses or trends using reasoning chains.
Report Builder Agent – Compiles all insights into a structured report
Any more agents you want to add

---

## 📌 What This Is

A fully autonomous, multi-agent research assistant that takes a complex question and runs it through a 5-agent LangGraph pipeline — planning, retrieving from 3 sources in parallel, analyzing, generating insights, and compiling a structured cited Markdown report.

```
Your Question
     ↓
🧠 Query Planner + Router     → breaks query into sub-queries, assigns tools
     ↓
🔍 Dynamic Retriever          → fires tools in parallel threads
   ├─ 🌐 Tavily Web Search    → live internet (sports, news, current events)
   ├─ 📚 ArXiv Academic Search → peer-reviewed papers (science, CS, physics)
   └─ 🗃️ ChromaDB Local Search → your uploaded PDFs
     ↓
🔬 Critical Analyst           → validates facts, flags contradictions
     ↓
💡 Insight Generator          → Chain-of-Thought reasoning, hypotheses
     ↓
📝 Report Builder             → structured Markdown report with citations
     ↓
Final Report (downloadable .md)
```

**Key Design — Dynamic Tool Routing:**  
The Planner acts as a triage nurse. "Virat Kohli IPL stats?" → web only. "Hawking radiation theory?" → ArXiv + web + local. The LLM decides which tools to call per sub-query — no hardcoded if-else logic.

---

## 🗂️ Project Structure

```
Shreya_Gupta/
└── Hackathon/                        # ← Project root. cd here before EVERYTHING.
    │
    ├── app.py                        # Streamlit entry point (run this)
    ├── requirements.txt              # All Python dependencies (pinned versions)
    ├── check_env.py                  # Sanity check — run before app.py
    ├── .env.example                  # Template for environment variables
    ├── .env                          # Your actual keys — gitignored, never committed
    ├── README.md                     # This file
    │
    ├── core/
    │   ├── __init__.py
    │   ├── state.py                  # LangGraph TypedDict state schema
    │   └── graph.py                  # DAG compilation (nodes + edges)
    │
    ├── agents/
    │   ├── __init__.py
    │   ├── planner.py                # Query Planner + Tool Router node
    │   ├── retriever.py              # Dynamic Retriever (parallel tool execution)
    │   ├── analyst.py                # Critical Analyst node
    │   ├── insight.py                # Insight Generator node
    │   └── reporter.py               # Report Builder node
    │
    ├── tools/
    │   ├── __init__.py
    │   ├── web_search.py             # Tavily web search tool
    │   ├── arxiv_search.py           # ArXiv academic paper search tool
    │   └── vector_store.py           # ChromaDB local vector store + PDF ingestion
    │
    ├── llm/
    │   ├── __init__.py
    │   └── openrouter.py             # LLM factory via OpenRouter API
    │
    └── chroma_db/                    # Auto-created on first PDF upload (gitignored)
```

> ⚠️ **The single most common mistake:** running commands from `Shreya_Gupta/` instead of `Shreya_Gupta/Hackathon/`. Python won't find the `core/`, `agents/`, `tools/` packages unless you're inside `Hackathon/`. Always `cd Hackathon` first.

---

## ⚙️ Prerequisites

Before you begin, make sure you have:

| Requirement | Version | Check Command |
|---|---|---|
| Python | 3.10 or 3.11 recommended | `python --version` |
| pip | Latest | `pip --version` |
| Git | Any recent version | `git --version` |
| Internet connection | Required for Tavily + ArXiv + OpenRouter | — |

> ⚠️ **Python 3.12+ may cause dependency conflicts** with some LangChain packages. Use 3.10 or 3.11 if possible.

---

## 🔑 API Keys Required

You need two API keys. Both have free tiers — no credit card required for basic usage.

### 1. OpenRouter API Key
- Go to: [https://openrouter.ai](https://openrouter.ai)
- Sign up → Dashboard → Keys → Create Key
- Looks like: `sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- Free credits given on signup. Top up as needed.

### 2. Tavily Search API Key
- Go to: [https://tavily.com](https://tavily.com)
- Sign up → API Keys → Copy key
- Looks like: `tvly-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- Free tier: **1,000 searches/month** — more than enough for development.

> 💡 ChromaDB and FastEmbed (local embeddings) are **completely free** — they run locally on your machine with no API key needed.

---

## 🚀 Setup & Installation — Step by Step

### Step 1 — Clone the repository

```bash
git clone https://github.com/eng-accelerator/Submissions_C5.git
cd Submissions_C5
git checkout Group_2
```

### Step 2 — Navigate to the project folder

```bash
cd Shreya_Gupta/Hackathon
```

Verify you are in the right place:

```bash
# Windows
dir

# Mac/Linux
ls -la
```

You should see `app.py`, `requirements.txt`, `check_env.py`, and the `core/`, `agents/`, `tools/`, `llm/` folders directly inside `Hackathon/`.

### Step 3 — Create a Python virtual environment

A virtual environment keeps this project's dependencies isolated from your system Python. Think of it as a dedicated toolbox for this project — what gets installed here stays here.

```bash
# Windows
python -m venv venv

# Mac/Linux
python3 -m venv venv
```

This creates a `venv/` folder inside `Hackathon/`. Your structure now looks like:

```
Hackathon/
├── venv/          ← created by this step
├── app.py
├── requirements.txt
└── ...
```

### Step 4 — Activate the virtual environment

> ⚠️ **Critical step.** You must activate the venv EVERY TIME you open a new terminal for this project. If you skip this, pip installs go to the wrong Python and you'll get `ModuleNotFoundError`.

```bash
# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Mac/Linux
source venv/bin/activate
```

✅ You'll know it worked when you see `(venv)` prefix in your terminal:

```
(venv) C:\Users\SHREYA\GitHub\Submissions_C5\Shreya_Gupta\Hackathon>
```

> 💡 **PowerShell tip:** If `Activate.ps1` is blocked, run this once to allow it:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### Step 5 — Upgrade pip

Old pip versions silently fail to resolve dependencies correctly. Always upgrade first.

```bash
python -m pip install --upgrade pip
```

### Step 6 — Install all dependencies

```bash
pip install -r requirements.txt
```

This takes **2-5 minutes** on first run — it downloads LangChain, LangGraph, ChromaDB, FastEmbed (including the ~130MB embedding model), and all transitive dependencies.

> ☕ Good time for a coffee break.

Expected output at the end:
```
Successfully installed langchain-0.3.25 langgraph-0.3.5 chromadb-0.6.3 ...
```

### Step 7 — Verify all packages installed correctly

Run the sanity check script **before** launching the app:

```bash
python check_env.py
```

Expected output:
```
Python executable: C:\...\Shreya_Gupta\Hackathon\venv\Scripts\python.exe

  ✅ langgraph                 0.3.5
  ✅ langchain                 0.3.25
  ✅ langchain_openai          0.3.16
  ✅ langchain_community       0.3.23
  ✅ langchain_chroma          0.2.4
  ✅ chromadb                  0.6.3
  ✅ fastembed                 0.4.2
  ✅ tavily                    0.5.0
  ✅ arxiv                     2.2.0
  ✅ streamlit                 1.44.1
  ✅ pypdf                     5.4.0
  ✅ pydantic                  2.11.3
  ✅ dotenv                    installed

🟢 All packages found. Safe to run: streamlit run app.py
```

> ⚠️ Confirm the Python path shows `Hackathon\venv\Scripts\python.exe` — NOT your system Python. If it points elsewhere, your venv is not activated.

If any package shows ❌:
```bash
pip install <package-name>
python check_env.py   # re-run to confirm
```

### Step 8 — (Optional but recommended) Set up environment variables

Instead of typing API keys in the UI every session, store them in a `.env` file. The app auto-loads this on startup.

```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

Open `.env` in any text editor and fill in your keys:

```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
TAVILY_API_KEY=tvly-your-actual-key-here
```

Save the file. No quotes needed around the values.

> 🔒 `.env` is listed in `.gitignore` — it will **never** be committed to GitHub. Safe to store real keys here locally.

---

## ▶️ Running the Application

### Confirm you are in the correct directory

```bash
# Windows — full path for clarity
cd C:\Users\SHREYA\GitHub\Submissions_C5\Shreya_Gupta\Hackathon

# Mac/Linux
cd ~/path/to/Submissions_C5/Shreya_Gupta/Hackathon
```

### Confirm venv is active

You must see `(venv)` at the start of your terminal prompt before running the app.

### Start the Streamlit app

```bash
streamlit run app.py
```

The terminal will show:

```
  You can now view your Streamlit app in your browser.

  Local URL:  http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Your browser should open automatically. If it doesn't, open [http://localhost:8501](http://localhost:8501) manually.

### Stop the app

Press `Ctrl + C` in the terminal.

---

## 🖥️ Using the UI — Walkthrough

### Sidebar (left panel)

| Section | What to do |
|---|---|
| **OpenRouter API Key** | Paste your `sk-or-v1-...` key |
| **Tavily Search API Key** | Paste your `tvly-...` key |
| **Save API Keys** | Click this button — keys persist for the session |
| **Model Selection** | Choose your LLM (Claude 3.5 Haiku recommended for speed) |
| **Upload PDF Documents** | Optional — upload research papers for local ChromaDB search |
| **Ingest into ChromaDB** | Click after uploading PDFs to chunk + embed them locally |

> 💡 If you set up `.env` in Step 8, your keys auto-load and you can skip manual entry entirely.

### Main Area

1. Type your research question in the text box
2. Click **🚀 Run Research**
3. Watch the **progress expander** — each agent checks in as it completes
4. The **Routing Plan** appears immediately after the Planner runs — shows which tools were assigned to each sub-query and why
5. After ~30-90 seconds (depends on model and query complexity), the full report appears

### Results Tabs

| Tab | Contents |
|---|---|
| **📄 Full Report** | Structured Markdown report with all 5 sections + download button |
| **🔍 Raw Documents** | Every chunk retrieved, filterable by tool (Web / ArXiv / Local) |
| **🗺️ Routing Details** | Exactly which tools the Planner assigned per sub-query and why |

### Timing Metrics Bar

At the top of every result you'll see 5 KPI cards:

```
⏱️ Total Time   📄 Doc Chunks   🌐 Web Results   📚 ArXiv Papers   🗃️ Local Chunks
    42.3s            18               8                 6                4
```

---

## 🧪 Example Queries to Test Dynamic Routing

Run these and check the **🗺️ Routing Details** tab each time to see the Planner's decisions:

```
# Routes to: tavily_web_search ONLY (real-time sports data)
What are Virat Kohli's IPL 2024 batting statistics?

# Routes to: arxiv_search + chroma_local (academic physics)
What is the latest research on Hawking radiation and the black hole information paradox?

# Routes to: arxiv_search + tavily_web_search + chroma_local (technical, mixed)
Compare Mamba state space models vs Transformer attention for long-context tasks.

# Routes to: tavily_web_search ONLY (recent tech news)
What caused the CrowdStrike global IT outage and its cybersecurity implications?

# Routes to: arxiv_search + tavily_web_search (biotech, mixed academic + news)
What are the latest breakthroughs in mRNA vaccine technology beyond COVID-19?
```

---

## 🐛 Troubleshooting

### `ModuleNotFoundError: No module named 'langgraph'`

Either venv is not activated, or you're running from the wrong directory. Fix both:
```bash
cd Shreya_Gupta/Hackathon    # ← must be inside Hackathon/, not Shreya_Gupta/
venv\Scripts\activate         # Windows
source venv/bin/activate      # Mac/Linux
streamlit run app.py
```

### `ModuleNotFoundError: No module named 'langchain.text_splitter'`

LangChain v0.3 moved this to a separate package. Fix:
```bash
pip install langchain-text-splitters
```

### `AttributeError: st.session_state has no attribute 'openrouter_key'`

Hard-refresh your browser (`Ctrl+Shift+R`) and restart Streamlit:
```bash
# Ctrl+C to stop, then:
streamlit run app.py
```

### `pip install` hangs or fails on `chromadb` or `fastembed`

Install these two with extended timeout first, then re-run the full requirements:
```bash
pip install chromadb --timeout 120
pip install fastembed --timeout 120
pip install -r requirements.txt
```

### API Key errors at runtime

- OpenRouter key must start with `sk-or-v1-`
- Tavily key must start with `tvly-`
- Check remaining credits at [openrouter.ai/dashboard](https://openrouter.ai/dashboard)

### Streamlit opens but app crashes immediately

```bash
python check_env.py
```
Fix any ❌ packages shown, then retry.

### ArXiv search returns no results

ArXiv rate-limits queries. The tool has a 1-second delay built in. Wait 10 seconds and retry with slightly different wording.

### Port 8501 already in use

```bash
streamlit run app.py --server.port 8502
```

---

## 📦 Tech Stack & Why Each Was Chosen

| Technology | Role | Why |
|---|---|---|
| **LangGraph** | Agent orchestration | Stateful DAG — each node reads/writes shared state cleanly |
| **LangChain** | LLM + tool abstractions | `@tool` decorator, `ChatOpenAI`, message types |
| **OpenRouter** | LLM API gateway | Access Claude, GPT-4, Gemini, Llama via one API key |
| **Tavily** | Live web search | Purpose-built for LLM agents — cleaner than raw Google scraping |
| **ArXiv** | Academic papers | 2M+ free preprints via official Python client |
| **ChromaDB** | Local vector store | 100% free, local, persistent, no cloud required |
| **FastEmbed** | Embeddings | Local, free, 33M param model — zero OpenAI embedding cost |
| **Streamlit** | Frontend | Python-native UI, `st.status` for real-time agent progress |
| **Pydantic** | Data validation | TypedDict state schema enforcement |

---

## 🏗️ Architecture Deep Dive

### Why LangGraph over a simple chain?

A basic LangChain chain is like an assembly line — each step runs blindly in sequence. LangGraph is a **stateful graph** — each node reads the full accumulated state, writes to specific fields, and the framework manages transitions safely.

```python
# The state is a TypedDict — shared whiteboard for all 5 agents
class ResearchState(TypedDict):
    user_query:     str
    sub_queries:    List[str]
    routing_plan:   List[SubQueryRoute]                # Planner's triage decisions
    raw_documents:  Annotated[List[...], operator.add] # accumulates across nodes
    analyzed_facts: str
    insights:       str
    final_report:   str
    current_agent:  str
    error:          Optional[str]
```

### Why parallel tool execution?

For a query like "Explain Hawking radiation", the Planner assigns 3 tools. Sequential would take 3× longer:

```
Sequential:  ArXiv(5s) → Tavily(3s) → ChromaDB(0.5s) = 8.5s total
Parallel:    All three fire simultaneously              = 5.0s total (slowest wins)
```

Implemented via `concurrent.futures.ThreadPoolExecutor` in `agents/retriever.py`.

### Why `operator.add` on `raw_documents`?

Without it, each node overwrites the previous documents. With it, they accumulate:

```python
raw_documents: Annotated[List[Dict], operator.add]
# Retriever adds 8 docs  → [doc1..doc8]
# Future nodes add more  → [doc1..doc8, doc9..docN]  ← safe accumulation
```

---

## 📁 `check_env.py` — Sanity Check Script

This file should already exist in `Hackathon/`. If it's missing, create it:

```python
# check_env.py — place in Shreya_Gupta/Hackathon/
import sys
print(f"Python executable: {sys.executable}")
print(f"Python version:    {sys.version}\n")

packages = [
    "langgraph", "langchain", "langchain_openai",
    "langchain_community", "langchain_chroma",
    "chromadb", "fastembed", "tavily", "arxiv",
    "streamlit", "pypdf", "pydantic", "dotenv",
]

all_ok = True
for pkg in packages:
    try:
        mod     = __import__(pkg)
        version = getattr(mod, "__version__", "installed")
        print(f"  ✅ {pkg:<28} {version}")
    except ImportError:
        print(f"  ❌ {pkg:<28} NOT FOUND")
        all_ok = False

print()
if all_ok:
    print("🟢 All packages found. Safe to run: streamlit run app.py")
else:
    print("🔴 Missing packages. Run: pip install -r requirements.txt")
    sys.exit(1)
```

---

## 🔐 Security Notes

- Never commit your `.env` file — it is listed in `.gitignore`
- Never hardcode API keys directly in any `.py` file
- The app stores keys in `st.session_state` only — never written to disk by the app
- ChromaDB lives in `Hackathon/chroma_db/` — local only, never uploaded anywhere

---

## 📜 License

MIT License — free to use, modify, and distribute with attribution.

---

## 👩‍💻 Author

**Shreya Gupta (d_u_u_u_h_h)**  
AI Accelerator Program — Cohort C5, Group 2  
GitHub: [eng-accelerator/Submissions_C5](https://github.com/eng-accelerator/Submissions_C5/tree/Group_2/Shreya_Gupta/Hackathon)

---

*Built with LangGraph · LangChain · ChromaDB · Streamlit · OpenRouter · Tavily · ArXiv*
