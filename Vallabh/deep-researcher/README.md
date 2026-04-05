# Multi-Agent AI Deep Researcher

A production-grade multi-agent research assistant for multi-hop, multi-source
investigations. The system spins up specialized agents that collaborate to retrieve,
analyze, synthesize, and report on any research topic.

### Demo Link
https://jumpshare.com/s/IZ8eBhRYBqpptX4ICYGN

## Architecture

```
User Query (Streamlit / CLI)
        │
        ▼
   Query Planner (decomposes into sub-questions)
        │
        ▼
   Orchestrator (LangGraph StateGraph)
        │
        ├──► Contextual Retriever Agent
        │       ├── ArXiv (research papers)
        │       ├── Wikipedia (background knowledge)
        │       ├── Tavily Web Search (news, reports, articles)
        │       └── Aggregates + deduplicates sources
        │
        ├──► Critical Analysis Agent
        │       ├── Summarizes findings per source
        │       ├── Highlights contradictions between sources
        │       ├── Validates source credibility
        │       └── Identifies information gaps
        │
        ├──► Fact Checker Agent
        │       ├── Cross-validates key claims across sources
        │       ├── Flags unsupported or contradicted claims
        │       └── Assigns confidence scores
        │
        ├──► Insight Generation Agent
        │       ├── Identifies emerging trends
        │       ├── Generates hypotheses from evidence
        │       ├── Builds reasoning chains
        │       └── Suggests future research directions
        │
        ├──► Conditional: Gap Filler (if critical gaps found)
        │       └── Runs additional retrieval for missing info
        │
        └──► Report Builder Agent
                ├── Compiles structured research report
                ├── Executive summary
                ├── Methodology section
                ├── Findings with citations
                ├── Confidence assessment
                └── Exports as Markdown / DOCX
```

## Sprint Plan

### Sprint 1: Foundation (State + Query Planner + Retriever)
- State schema with Pydantic models
- Query Planner (decomposes complex queries into sub-questions)
- Contextual Retriever Agent (ArXiv, Wikipedia, Tavily)
- Source deduplication and relevance scoring

### Sprint 2: Analysis + Fact Checking
- Critical Analysis Agent (summarize, find contradictions, validate)
- Fact Checker Agent (cross-validate claims, confidence scoring)
- Gap detection logic

### Sprint 3: Insight Generation + Report Builder
- Insight Generation Agent (trends, hypotheses, reasoning chains)
- Report Builder Agent (structured markdown/docx output)
- Conditional gap-filling loop

### Sprint 4: UI + Orchestrator + Testing
- LangGraph StateGraph with conditional edges
- Streamlit UI with real-time progress
- Export to Markdown
- Comprehensive tests

## Tech Stack

| Layer              | Technology                                      |
|--------------------|------------------------------------------------|
| Orchestration      | LangGraph StateGraph with conditional edges     |
| LLM                | OpenAI GPT-4o via LangChain                    |
| Structured Output  | Pydantic v2 with `with_structured_output()`     |
| Research Sources   | ArXiv API, Wikipedia, Tavily Web Search         |
| UI                 | Streamlit                                        |
| Observability      | LangSmith tracing                                |
| CLI Output         | Rich                                             |

## Setup

```bash
cd deep-researcher
python -m venv venv
source venv/bin/activate        # Linux/Mac
# .\venv\Scripts\Activate.ps1  # Windows PowerShell

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your API keys (minimum: OPENAI_API_KEY)

# Run via CLI
python main.py --query "What are the latest advances in quantum error correction?"

# Run Streamlit UI
streamlit run ui/app.py
```

## Project Structure

```
deep-researcher/
├── main.py                     # CLI entry point
├── requirements.txt
├── .env.example
├── config/
│   └── __init__.py             # App configuration
├── state/
│   └── __init__.py             # LangGraph state + Pydantic models
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py         # LangGraph StateGraph
│   ├── query_planner.py        # Decomposes query into sub-questions
│   ├── retriever.py            # Multi-source retrieval agent
│   ├── analyzer.py             # Critical analysis agent
│   ├── fact_checker.py         # Cross-validation agent
│   ├── insight_generator.py    # Hypothesis & trend agent
│   ├── gap_filler.py           # Targeted retrieval for gaps
│   └── report_builder.py       # Structured report agent
├── tools/
│   ├── __init__.py
│   ├── arxiv_tool.py           # ArXiv paper search
│   ├── wikipedia_tool.py       # Wikipedia search
│   └── tavily_tool.py          # Web search via Tavily
├── ui/
│   └── app.py                  # Streamlit interface
└── tests/
    ├── test_planner.py
    ├── test_retriever.py
    ├── test_analyzer.py
    └── test_orchestrator.py
```
