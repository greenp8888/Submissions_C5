# Local-First Multi-Agent AI Deep Researcher Architecture

## 1. Purpose

This solution turns the original notebook-based **RAG + single-agent router** into a **local-first, Gradio-powered, LangGraph-orchestrated research assistant**.

It is designed for hackathon delivery under tight time constraints, with these priorities:

1. **Runs on the user's own machine first**
2. **Can optionally be exposed through a public tunnel later**
3. **Produces a structured research report**
4. **Feels like a true multi-agent workflow, not just a chatbot with search**

---

## 2. Design Principles

### Local-first
- The app runs on `localhost` by default.
- No cloud hosting is required for the core demo.
- Public sharing is optional and can be added later via Gradio sharing or a tunnel.

### Deterministic graph over agent chaos
- This is implemented as a **LangGraph workflow** rather than a free-form tool-calling agent.
- The graph follows a predictable order:
  1. Planner
  2. Retriever
  3. Critical Analyst
  4. Insight Generator
  5. Report Builder

### Reuse over rewrite
The original notebook already solved several important problems:
- OpenRouter LLM integration
- PDF ingestion and chunking
- FAISS vector retrieval
- External information access patterns
- Query orchestration mindset

This solution preserves those strengths while replacing the top-level single-agent flow with a multi-agent state graph.

---

## 3. Scope of the MVP

### Included
- Multiple PDF upload
- Local vector search over uploaded PDFs
- Optional live web retrieval through Tavily
- Optional academic retrieval through arXiv
- Wikipedia background retrieval
- LangGraph-based multi-step research flow
- Structured markdown report
- Gradio UI
- Downloadable markdown report

### Deferred
- User authentication
- Persistent database
- Multi-user sessions
- Human-in-the-loop approvals
- Citation styling beyond practical markdown references
- Deep source deduplication across domains
- Long-term memory across runs

---

## 4. High-Level Architecture

```text
+----------------------+
|      Gradio UI       |
|  - question input    |
|  - PDF upload        |
|  - toggles / options |
|  - report display    |
+----------+-----------+
           |
           v
+----------------------+
|   run_research()     |
|  app entrypoint      |
+----------+-----------+
           |
           v
+------------------------------+
| LangGraph StateGraph         |
|                              |
|  START                       |
|    -> planner                |
|    -> retriever              |
|    -> critical_analyst       |
|    -> insight_generator      |
|    -> report_builder         |
|    -> END                    |
+------------------------------+
           |
           v
+------------------------------+
| Shared Research State        |
|  - question                  |
|  - subquestions              |
|  - evidence[]                |
|  - critique                  |
|  - contradictions            |
|  - insights                  |
|  - final_report              |
+------------------------------+
```

**Current LangGraph (Phase 2):** conditional routing, follow-up retrieval, and duplicate terminal chains are **not** shown in the sketch above. For an accurate node/edge diagram, see **[GRAPH.md](./GRAPH.md)** (Mermaid).

---

## 5. Agent Responsibilities

## 5.1 Planner Agent
**Goal:** Turn a broad research question into focused sub-questions.

### Inputs
- User question

### Outputs
- Research objective
- 4–6 sub-questions
- Suggested investigation emphasis

### Why it exists
This makes the system feel like a researcher that plans before searching.

---

## 5.2 Contextual Retriever Agent
**Goal:** Gather evidence from available sources.

### Sources
- Uploaded PDFs via FAISS
- Tavily web search
- arXiv paper metadata and summaries
- Wikipedia summaries

### Outputs
A normalized list of evidence objects:
- source type
- title
- url
- excerpt
- relevance hint
- source label

### Why it exists
This is the evidence collection layer. It is the main reuse of the notebook's RAG core.

---

## 5.3 Critical Analysis Agent
**Goal:** Evaluate what the evidence says and where it disagrees.

### Outputs
- key findings
- contradictions
- evidence quality notes
- research gaps

### Why it exists
Retrieval alone is not deep research. The critical analyst is what upgrades the workflow from search to investigation.

---

## 5.4 Insight Generation Agent
**Goal:** Move from “what was found” to “what it might mean.”

### Outputs
- trends
- implications
- hypotheses
- next-step questions

### Why it exists
This gives judges a visible reasoning layer beyond summarization.

---

## 5.5 Report Builder Agent
**Goal:** Assemble a polished final artifact.

### Outputs
A structured markdown report:
- question
- method
- sources consulted
- findings
- contradictions and caveats
- insights
- conclusion
- references

### Why it exists
Hackathon demos are stronger when the system produces a concrete deliverable.

---

## 6. Shared State Model

The LangGraph state carries the full research context across nodes.

### Core state fields
- `question`
- `pdf_paths`
- `enable_web_search`
- `top_k`
- `web_results_per_query`
- `subquestions`
- `evidence`
- `analysis_summary`
- `contradictions`
- `insights`
- `final_report`
- `trace`

### Why shared state matters
This is what makes the app a multi-agent workflow instead of a sequence of isolated function calls.

---

## 7. Retrieval Strategy

## 7.1 Uploaded PDFs
- PDF text is loaded and chunked
- embeddings are generated
- a FAISS index is created
- each sub-question is queried against the local index

### Notes
- This is ephemeral by default for simplicity
- perfect for personal/local use
- avoids any external storage dependency

## 7.2 Tavily
Used only when:
- the toggle is enabled
- an API key is present

Best for:
- recent developments
- product/vendor information
- news and web pages

## 7.3 arXiv
Best for:
- technical and academic topics
- research paper signals
- paper titles and abstracts

## 7.4 Wikipedia
Best for:
- definitions
- broad background
- stable foundational knowledge

---

## 8. UI Architecture

The UI is intentionally simple:
- one question box
- optional PDF uploads
- toggle for web search
- report output
- evidence table
- trace panel
- downloadable markdown file

### Why not over-design the UI?
Because the value in this hackathon lies in:
- agent orchestration
- evidence synthesis
- report generation

The UI should stay reliable and lightweight.

---

## 9. Local Hosting Model

### Default mode
- Runs on `127.0.0.1`
- Accessible only from the host machine

### Optional LAN mode
- Bind to `0.0.0.0`
- Accessible from devices on the same network

### Optional public demo mode
- Keep the app local but expose it through:
  - Gradio share link, or
  - a separate tunnel like ngrok

This means the **application logic still runs on the user's laptop**, even when a public URL is used.

---

## 10. Failure Handling and Fallbacks

### Missing Tavily key
- App still works using PDFs, Wikipedia, and arXiv

### No PDFs uploaded
- App still works as a web + paper researcher

### No web search enabled
- App still works as a local document + academic assistant

### LLM planning fails to return clean JSON
- Fallback parser extracts bullet lines
- Final fallback uses the original question only

### Weak retrieval
- Report explicitly notes limited evidence rather than pretending certainty

---

## 11. Why this architecture is feasible by tomorrow

Because it deliberately avoids:
- backend/frontend split deployment
- authentication
- database provisioning
- async job infrastructure
- advanced memory systems

Instead, it focuses on:
- one local app
- one graph
- one clear demo story

That is the right tradeoff for a hackathon submission deadline.

---

## 12. Recommended Demo Narrative

> “This is a local-first multi-agent deep researcher. It can run privately on my own machine, investigate a question across uploaded PDFs and external sources, critique contradictions, generate insights, and compile a structured report. The orchestration is handled by LangGraph, so the workflow is transparent and extensible.”

---

## 13. Repo Layout

```text
multi_agent_deep_researcher_local/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── ARCHITECTURE.md
└── deep_researcher/
    ├── __init__.py
    ├── config.py
    ├── models.py
    ├── retrieval.py
    └── graph.py
```

---

## 14. Build Strategy From the Original Notebook

### Reused from notebook
- OpenRouter configuration pattern
- document chunking
- FAISS retrieval
- general multi-source research intent

### Replaced
- single ReAct agent
- simple RAG-or-fallback router
- notebook-bound interaction model

### Added
- LangGraph state orchestration
- specialist research nodes
- normalized evidence model
- Gradio interface
- report export

---

## 15. Future Extensions

After the hackathon, this can evolve into:
- persistent vector indexes
- source quality scoring
- analyst personas
- timeline extraction
- report templates by domain
- LangSmith tracing
- local database storage
- cloud deployment on Render
