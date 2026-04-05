# Autonomous Multi-Agent Research Assistant -- Code Guide

## AI Agent Concepts

### What is a Deep Research Agent?

A Deep Research Agent is an autonomous system that mimics how a human researcher tackles extensive questions:
1. **Understand & Map** -- decompose an otherwise complex or ambiguous query into targeted sub-questions.
2. **Retrieve Information** -- pull accurate raw data from specific tools targeting academic papers, real-time web content, or localized PDFs.
3. **Filter & Evaluate** -- critically assess information to weed out redundancy and find cross-source harmony or dissonance.
4. **Hypothesize** -- synthesize deep reasoning models to establish actionable conclusions.
5. **Report** -- format raw metadata into an easy-to-digest documented resource with appropriate citations.

Unlike a standard RAG system (Retriever-Augmented Generation) that blindly throws a user's prompt against a vector database and an LLM context window—our Deep Research Agent uses a robust state machine that verifies query routing and executes dynamically.

### System Flow
The architecture dictates execution in this strict order:
*Planner* → *Retriever* → *Analyst* → *Insight Generator* → *Reporter*.

---

## LangGraph Orchestration Constructs

The project utilizes `langgraph` instead of raw `langchain` agents.

### The Application State (`core/state.py`)

A state machine needs a "whiteboard" to pass arguments between functions. The `ResearchState` uses Python's `TypedDict`.

```python
from typing import Annotated, Dict, List, Optional
from typing_extensions import TypedDict
import operator

class ResearchState(TypedDict):
    user_query: str
    sub_queries: List[str]
    routing_plan: List[Dict]
    
    # Annotated with operator.add enables the state property to act as a 
    # persistent accumulating list across parallel map/reduce tasks!
    raw_documents: Annotated[List[Dict], operator.add]
    
    analyzed_facts: str
    insights: str
    final_report: str
    current_agent: str
    error: Optional[str]
```

### Graph Compilation (`core/graph.py`)

LangGraph explicitly defines node topology to prevent circular reasoning loops.

```python
from langgraph.graph import StateGraph, END
from core.state import ResearchState
import agents.planner, agents.retriever, etc.

def build_research_graph(openrouter_api_key, model):
    workflow = StateGraph(ResearchState)

    # 1. Add Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("retriever", retriever_node)
    
    # ... more nodes
    
    # 2. Define Edges (Routing)
    workflow.add_edge("planner", "retriever")
    workflow.add_edge("retriever", "analyst")
    # ... more edges
    
    # 3. Define Entry and Exit
    workflow.set_entry_point("planner")
    workflow.add_edge("reporter", END)

    return workflow.compile()
```

---

## Component Implementation Patterns

### LLM Node Execution Pattern

An agent node is simply a Python function that accepts `state` and an initialized `llm`. It reads what it needs, performs calculations via the LLM, and returns only the parts of the state it needs to update. 

```python
def planner_node(state: ResearchState, llm):
    query = state["user_query"]
    
    system_prompt = "You are a research planner. Break this into sub-queries."
    # API invocation
    response = llm.invoke([SystemMessage(system_prompt), HumanMessage(query)])
    
    # The dictionary returned gets intelligently merged by LangGraph
    return {
        "sub_queries": ["Q1", "Q2"],
        "routing_plan": [...],
        "current_agent": "Planner"
    }
```

### Parallel Tool Execution (Retriever)

Instead of the LLM serially deciding which tool to call next, the `retriever.py` node manually forks threads based on the Planner's `routing_plan`, significantly decreasing latency.

```python
import concurrent.futures

def retriever_node(state: ResearchState):
    plan = state.get("routing_plan", [])
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for p in plan:
            if "tavily_web_search" in p.get("tools", []):
                futures.append(executor.submit(run_tavily, p["sub_query"]))
            if "arxiv_search" in p.get("tools", []):
                futures.append(executor.submit(run_arxiv, p["sub_query"]))
                
        for future in concurrent.futures.as_completed(futures):
            results.extend(future.result())

    # Safely accumulated since `raw_documents` uses operator.add
    return {"raw_documents": results, "current_agent": "Retriever"}
```

---

## Tool Implementations

### LangChain `@@tool` Wrapper

Tools abstract real-world APIs like Tavily or ArXiv into callable dictionaries designed for JSON ingestion.

```python
from langchain_core.tools import tool

@tool
def tavily_web_search(query: str, max_results: int = 5) -> str:
    """A search engine optimized for comprehensive, accurate, and trusted results. Useful for when you need to answer questions about current events."""
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    response = client.search(query=query, search_depth="advanced")
    return format_results(response)
```

Docstrings in `@tool` functions are critically important as the LangGraph LLMs utilize the docstring characters internally to map intent!

---

## Key Libraries

| Library | Purpose |
|---------|---------|
| `langgraph` | Application orchestration (DAG, persistence, routing). |
| `langchain_core` | Structural definitions like `HumanMessage` & `@tool`. |
| `langchain_openai` | Translates LangGraph commands for the OpenRouter provider. |
| `tavily-python` | Wrapper for Web Search SDK. |
| `pypdf` | Document loader for parsing PDFs to be ingested into ChromaDB. |
| `chromadb` | Light-weight local SQL-based semantic vector store. |
| `fastembed` | Inference engine for embeddings algorithm (`bge-small`) |
| `streamlit` | Reactive UI framework mapping graphs tracking logic onto a browser view. |
