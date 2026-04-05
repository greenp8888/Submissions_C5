# Product Requirements Document (PRD)

## Project: Multi-Agent AI Deep Researcher

### 1. Overview
This document specifies the core requirements, architecture mapped to implementation, and enhanced add-on capabilities for the **Multi-Agent AI Deep Researcher** application. The system is designed to be an AI-powered research assistant for multi-hop, multi-source investigations. 

---

### 2. Original Requirements Mapping

The primary objective of this project was to showcase agent collaboration, retrieval-augmented reasoning, and long-context synthesis utilizing frameworks such as LangChain, LangGraph, and LlamaIndex. Below is the direct mapping of the original target agents to their executed implementations.

#### 2.1 Contextual Retriever Agent ✅
* **Scope:** Pulls data from research papers, news articles, reports, and APIs.
* **Implementation:** Completed in `agents/retriever.py`. The `retriever_node` utilizes parallel thread execution to pull data dynamically from different sources based on the query. It integrates:
  - Live web searches via `tavily_web_search` (news, real-time data)
  - Research papers via `arxiv_search` (academic data)
  - Local documents via `chroma_local_search` (user-uploaded PDFs)

#### 2.2 Critical Analysis Agent ✅
* **Scope:** Summarizes findings, highlights contradictions, and validates sources.
* **Implementation:** Completed in `agents/analyst.py`. The `analyst_node` processes raw retrieved documents and acts as a skeptic. The LLM is prompted to output structured headers for **Validated Facts**, **Contradictions & Conflicts**, and **Source Quality Assessment**, ensuring high fidelity of information before synthesis.

#### 2.3 Insight Generation Agent ✅
* **Scope:** Suggests hypotheses or trends using reasoning chains.
* **Implementation:** Completed in `agents/insight.py`. The `insight_node` takes the validated facts from the critical analyst and employs explicit Chain-of-Thought (CoT) reasoning. It synthesizes non-obvious **Key Insights** and specific testable **Hypotheses** along with strategic implications for the user.

#### 2.4 Report Builder Agent ✅
* **Scope:** Compiles all insights into a structured report.
* **Implementation:** Completed in `agents/reporter.py`. The `report_builder_node` systematically pulls downstream outputs (facts, insights, logic chains) into a final, structured Markdown report utilizing concrete citation mechanisms to mitigate hallucination risks.

#### 2.5 Query Planner & Router Agent (Bonus) ✅
* **Scope:** Intelligent query decomposition and tool routing.
* **Implementation:** Completed in `agents/planner.py`. This fifth triage agent intercepts the user's initial expansive question, decomposes it into targeted sub-queries, and programmatically decides which extraction tools the Retriever agent should utilize per sub-query.

---

### 3. Additional Enhancements (Add-ons)
While meeting the foundational goals, several advanced, production-grade features were actively deployed to distinguish this platform from basic MVP proofs-of-concept. 

#### 3.1 🛠️ LangSmith Integration
* **Implementation Scope:** Deep observability and tracing framework.
* **Purpose:** Native integration with LangSmith makes the multi-agent LLM calls completely transparent. We monitor execution paths, token telemetry, latency spikes, and pinpoint edge-case failures across all tool interactions automatically.

#### 3.2 📁 Local PDF Upload & Offline Vector Search
* **Implementation Scope:** Local Vector Store ingestion engine using ChromaDB and FastEmbeds.
* **Purpose:** Alongside web-based APIs (ArXiv, Tavily), the application securely parses and ingests user-uploaded PDFs directly into a local SQLite-based ChromaDB instance allowing for 100% private, contextual RAG queries overlaid on top of public internet data. 

#### 3.3 🖥️ Streamlit Cloud Deployment
* **Implementation Scope:** Interactive UI & Cloud SaaS deployment.
* **Purpose:** The system runs beyond local CLI scripts. We wrapped the intricate LangGraph state machines into an intuitive, responsive Streamlit User Interface. Features include dynamic model selections, theme toggling, transparent agent status alerts, and Markdown report exporting. 

#### 3.4 🧪 Robust Pytest Test Suite
* **Implementation Scope:** Automated UI testing infrastructure.
* **Purpose:** Built robust testing automation using `pytest` alongside Streamlit's `AppTest` framework to validate core structural logic without incurring LLM API costs. This ensures the application remains highly stable and regress-resistant as the agent topography expands.

---

### 4. Technical Stack Highlights
- **Orchestration:** LangGraph (State Graph Management)
- **Framework:** LangChain Base
- **Frontend / Deployment:** Streamlit / Streamlit Cloud
- **Tracing:** LangSmith
- **Embeddings / Local Storage:** FastEmbed (`bge-small`), Chroma DB
- **API Endpoints:** OpenRouter API (LLMs), Tavily API (Search), ArXiv API (Scholars)
