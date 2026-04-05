# Autonomous Research Assistant — Architecture

## System Overview

The Autonomous Research Assistant is a multi-agent Directed Acyclic Graph (DAG) system that autonomously researches complex topics by combining live web search, academic databases, and local vector retrieval. It dynamically breaks down questions into sub-questions, routes them to optimal retrieval tools, evaluates the findings, and synthesizes a structured Markdown report.

Unlike monolithic chatbot LLM queries, this system orchestrates **5 separate AI agents** acting as specialized nodes in a LangGraph state machine, ensuring tasks like query decomposition, retrieval, and reasoning are isolated for optimal focus and reliability.

## Design Philosophy

The system follows a **Graph-based State Machine** orchestration model. The internal data model is built using a Python `TypedDict` (`ResearchState`). Each agent acts as a function (node) that receives the state, performs its singular localized task, and updates specific fields in the state. 

This functional architecture enables:
1. **Parallel Execution**: Retrieval calls run asynchronously and independently.
2. **Determinism**: Control flow is explicitly laid out via LangGraph graph edges rather than purely stochastic LLM-based prompting.
3. **Modularity**: Individual agents or retrieval tools can be swapped out without affecting the overall pipeline logic.

## Agentic Design Patterns Applied

| # | Pattern | How It's Applied |
|---|---------|-----------------|
| 1 | **Graph-based State Management** | Uses LangGraph to manage `ResearchState`. Each agent adds directly to properties via `operator.add` without destructing previous data. |
| 2 | **Prompt Chaining** | Sequential pipeline chain: Planner → Retriever → Analyst → Insight Generator → Reporter. |
| 3 | **Routing (Dynamic Triaging)** | The Planner Agent acts as a triage nurse, evaluating queries and mapping them to tools beforehand (e.g. `tavily_web_search`, `arxiv_search`, `chroma_local`). |
| 4 | **Parallelization** | The Dynamic Retriever node executes all planned sub-queries across multiple retrieval tools simultaneously using thread pooling. |
| 5 | **Tool Use** | LangChain `@tool` abstractions for web (Tavily), academia (ArXiv), and Vector Knowledge Bases (ChromaDB). |

## Agent Architecture

### Agent Responsibilities

#### 1. Query Planner + Router (Entry Point)
- **Role**: Query decomposition, intent classification, and tool assignment.
- **Action**: Takes the complex prompt and dissects it into 3-5 sub-queries. It pairs each sub-query with specific retrieval tools required to find the answer.
- **Output**: Populates the `routing_plan` field in `ResearchState`.

#### 2. Dynamic Retriever
- **Role**: High-speed, parallel data collection.
- **Action**: Parses the Planner's `routing_plan`. Spawns parallel worker threads to execute `tavily_web_search`, `arxiv_search`, and `chroma_local`.
- **Output**: Appends raw string responses and snippets to `raw_documents` collection.

#### 3. Critical Analyst
- **Role**: Fact-checking, noise filtering, and structuring.
- **Action**: Reads the messy arrays of `raw_documents`, filters out redundant info, validates core factual premises, and highlights cross-source contradictions.
- **Output**: Writes verified findings to `analyzed_facts`.

#### 4. Insight Generator
- **Role**: Chain-of-Thought strategic reasoning and hypothesis generation.
- **Action**: Looks past factual retrieval and uses the LLM to identify underlying trends, meaning, and actionable implications based strictly on `analyzed_facts`.
- **Output**: Updates the `insights` field.

#### 5. Report Builder (Terminal Node)
- **Role**: Final document synthesis and formatting.
- **Action**: Ingests all data across the `ResearchState` to create a coherent, beautifully formatted Markdown report, complete with cited references using APA style principles.
- **Output**: Updates the `final_report` field.

### Graph Topology

```
                  ┌──────────────┐
                  │User Query    │
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │              │
                  │   Planner    │
                  │              │
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │              │
                  │  Retriever   │ (Fires Tavily, ArXiv, ChromaDB in parallel)
                  │              │
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │              │
                  │   Analyst    │
                  │              │
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │              │
                  │  Insight     │
                  │  Generator   │
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │              │
                  │  Reporter    │
                  │ (Terminal)   │
                  └──────────────┘
```

## Data Architecture

### Context Object (ResearchState)

The `ResearchState` TypedDict serves as the **run context** passed to all nodes in the DAG. LangGraph injects data incrementally:

```python
class ResearchState(TypedDict):
    user_query:     str                                # Raw query
    sub_queries:    List[str]                          # Decomposed tasks
    routing_plan:   List[SubQueryRoute]                # Tool strategy
    raw_documents:  Annotated[List[Dict], operator.add]# Concurrent accumulation
    analyzed_facts: str                                # Filtered data
    insights:       str                                # Chain of thought
    final_report:   str                                # Final Markdown
    current_agent:  str                                # Tracking metadata
    error:          Optional[str]                      # Graceful degradation
```

### External & Local API Infrastructure

| Service | Architecture Layer | Cost Factor | Rate Limits / Auth |
|---------|-------------------|-------------|--------------------|
| OpenRouter | LLM Inference (Gateway) | Varying (Paid/Free) | Requires API Key |
| Tavily | Live Information Retrieval | Free tier limits | Requires API Key |
| ArXiv | Academic Document Search | Free | Unlimited (Rate-limited locally) |
| ChromaDB | Knowledge Base Storage | Zero Cost (Local SQLite) | Unlimited |
| FastEmbed | Embedding Inference (`bge-small`) | Zero Cost (Local CPU Compute) | Unlimited |

## Executable Flow

### 1. User Inputs Data
Using the Streamlit interface (`app.py`), the User interacts with the UI inputs and clicks "Run Research".

### 2. Streamlit to LangGraph Dispatch
The frontend compiles the Graph calling the OpenRouter factory (`llm.openrouter.py`) and passes the initial `ResearchState` object dictionary to the `.stream()` iterator.

### 3. Progressive Edge Transitions
Each agent completes its work synchronously block by block (with Retriever executing sub-threads simultaneously). Streamlit listens to `current_agent` state keys and dynamically checks off graphical boxes on the frontend.

### 4. Reporting
Once the Report Builder terminates graph execution, the application transitions control back to Streamlit completely to display the results, tool metrics, and data explorer arrays.
