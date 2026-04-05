# Autonomous Multi-Agent Research Assistant -- Tools Guide

## The Tooling Ecosystem
Tools act as the sensory inputs for the research assistant. They provide structured, deterministic access to external information silos—passing normalized data objects into the Retriever node. 

Tools are wrapped using LangChain's `@tool` decorator, which structurally parses python docstrings and function signatures to automatically map them to the downstream routing structures.

---

## Tool Implementations

### 1. Web Search (`web_search.py`)
**Function:** `tavily_web_search(query)`  
**Data Context:** Live Internet / Open Web  
**Primary Integration:** [Tavily API](https://tavily.com/)

**Operational Responsibilities:**
- Targets real-time information, breaking news, sports statistics, current events, and corporate press releases.
- Provides dual-layered extraction: It captures standard standard URLs alongside an intrinsic "AI Answer" generated dynamically by Tavily's model snippet analysis.
- Gracefully mitigates and handles API key absences or search failures to avoid halting parallel ThreadPool execution upstream.

### 2. ArXiv Academic Search (`arxiv_search.py`)
**Function:** `arxiv_search(query)`  
**Data Context:** Peer-Reviewed STEM Research & Preprints  
**Primary Integration:** `arxiv` Python SDK

**Operational Responsibilities:**
- Specializes exclusively in complex, technical queries related to Physics, Computer Science, Biology, and Economics.
- Structures results specifically to extract `Title`, `Authors`, and `Published Date` along with truncated Abstracts to prevent token limit breaches.
- Operates under strict rate-limiting protocol (`delay_seconds=1.0`) ensuring compliance with academic hosting platforms.

### 3. Local Vector Store (`vector_store.py`)
**Function:** `chroma_local_search(query)` (Tool) / `ingest_pdf_to_chroma(file)` (Pipeline)  
**Data Context:** Private Document Ingestion (PDFs)  
**Primary Integration:** `ChromaDB` / `FastEmbedEmbeddings`

**Operational Responsibilities:**
- Controls an end-to-end local data pipeline. Processes Streamlit temporary file objects → parses text via `PyPDFLoader` → chunks using `RecursiveCharacterTextSplitter`.
- Ingests data through the localized `BAAI/bge-small-en-v1.5` embedding model, entirely bypassing third-party cloud API costs.
- Queries its `research_docs` vector collection via high-accuracy similarity ranking.
- Intelligent pre-flight checks: Analyzes ChromaDB collection capacity to actively intercept and abort empty queries when the user hasn't uploaded prior context.
