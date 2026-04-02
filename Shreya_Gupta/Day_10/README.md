# 🧠 Agentic RAG — LangChain + FAISS + Streamlit

> **Architecture:** PDF → FAISS RAG → LangChain Agent → Wikipedia / Tavily / ArXiv

---

## 📐 Architecture

```
User Query
    │
    ▼
PDF uploaded?
    ├── YES ──→ RAG (FAISS + PDF)
    │               │
    │           Answer found?
    │               ├── YES ──→ Return PDF answer ✅
    │               └── NO  ──→ LangChain Agent ↓
    │
    └── NO  ──→ LangChain Agent
                    │
          ┌─────────┼──────────┐
          ▼         ▼          ▼
     Wikipedia   Tavily      ArXiv
    (encyclop.) (web/live) (research)
          │         │          │
          └─────────┴──────────┘
                    │
              Response + Source URL
```

---

## 🚀 Setup & Run

### 1. Clone / copy the project
```bash
cd agentic_rag
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate          # macOS/Linux
venv\Scripts\activate             # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API keys
```bash
cp .env.example .env
# Open .env and fill in:
#   OPENAI_API_KEY=sk-...
#   TAVILY_API_KEY=tvly-...
```

Get your keys:
- **OpenAI**: https://platform.openai.com/api-keys
- **Tavily**: https://app.tavily.com/ (free tier: 1000 searches/month)

### 5. Run the app
```bash
streamlit run app.py
```

---

## 📁 Project Structure

```
agentic_rag/
│
├── app.py                  ← Streamlit UI + routing logic
│
├── utils/
│   ├── rag_engine.py       ← PDF ingestion + FAISS + RetrievalQA
│   └── agent.py            ← LangChain ReAct agent builder
│
├── tools/
│   └── search_tools.py     ← Wikipedia / Tavily / ArXiv wrappers
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔧 Key Components

| Component | Library | Purpose |
|---|---|---|
| PDF Loader | `PyPDFLoader` | Parse PDF pages into Documents |
| Chunking | `RecursiveCharacterTextSplitter` | Split into 800-char chunks |
| Embeddings | `text-embedding-3-small` | OpenAI embeddings |
| Vector Store | `FAISS` | Local in-memory similarity search |
| QA Chain | `RetrievalQA` | Stuff chain with custom prompt |
| Agent | `create_react_agent` | ReAct reasoning + tool selection |
| Web Search | `TavilySearchResults` | Live web search |
| Encyclopedia | `WikipediaQueryRun` | Background knowledge |
| Research | `ArxivQueryRun` | Academic papers |
| UI | `Streamlit` | Chat interface |

---

## 💡 How Routing Works

1. **PDF uploaded?** → Try RAG first (FAISS cosine similarity)
2. **Answer found in PDF?** → Return with page citations
3. **NOT_FOUND_IN_PDF or no PDF** → LangChain ReAct agent kicks in
4. **Agent reasons** which tool fits best:
   - *Encyclopedic / historical* → Wikipedia
   - *Current events / docs / news* → Tavily
   - *ML / science / research* → ArXiv
5. **Response returned** with source badge + ReAct trace (expandable)

---

## ⚙️ Configuration Tuning

In `utils/rag_engine.py`:
```python
CHUNK_SIZE = 800          # increase for longer context, decrease for precision
CHUNK_OVERLAP = 150       # overlap to avoid cutting mid-sentence
TOP_K_DOCS = 4            # number of chunks retrieved per query
```

In `utils/agent.py`:
```python
model="gpt-4o-mini"       # swap to "gpt-4o" for higher quality
max_iterations=6          # max ReAct loops before giving up
```

---

## 🐛 Troubleshooting

| Issue | Fix |
|---|---|
| `ModuleNotFoundError` | Activate venv + `pip install -r requirements.txt` |
| `AuthenticationError` | Check `.env` has correct API keys |
| `Tavily rate limit` | Free tier = 1000/month; upgrade or throttle |
| PDF answer wrong | Lower `SIMILARITY_THRESHOLD` or increase `TOP_K_DOCS` |
| Agent loops too long | Reduce `max_iterations` in `agent.py` |
