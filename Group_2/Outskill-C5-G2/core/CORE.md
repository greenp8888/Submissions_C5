# Core Pipeline (core/)

This directory contains the **brain** of the Autonomous Research Assistant.

It implements a **multi-agent system** using **LangGraph**, where each agent has a specialized role. The agents work together in a pipeline to decompose queries, retrieve information, analyze it, and generate a final report.

## 📁 Directory Structure

```
core/
├── graph.py              # 🏗️ Graph definition and builder
├── state.py              # 💾 State management (ResearchState)
├── agents/
│   ├── planner.py        # 🎯 Query decomposition and routing
│   ├── retriever.py      # 🔍 Parallel data retrieval
│   ├── analyst.py        # 📊 Fact-checking and analysis
│   ├── insight_generator.py # 🧠 Strategic reasoning
│   └── reporter.py       # 📝 Report synthesis
└── utils/
    ├── logger.py         # 🪵 Logging utilities
    └── prompts.py        # 📝 Prompt templates
```

## 🧩 Agent Architecture

The system follows this pipeline :

```
User Query → Planner → Retriever → Analyst → Insight Generator → Reporter → Final Report
```

### 1. 🎯 Query Planner (planner.py)
- **Role**: Decomposes complex queries into smaller, manageable sub-queries
- **Action**: Uses LLM to identify sub-tasks and determines which tools to use for each
- **Output**: `routing_plan` with sub-queries and tool assignments

### 2. 🔍 Dynamic Retriever (retriever.py)
- **Role**: Parallel data collection
- **Action**: Executes all sub-queries using multiple tools (web search, academic papers, local knowledge base)
- **Output**: `raw_documents` with search results

### 3. 📊 Critical Analyst (analyst.py)
- **Role**: Fact-checking and analysis
- **Action**: Filters out irrelevant information, validates facts, identifies contradictions
- **Output**: `analyzed_facts` with verified information

### 4. 🧠 Insight Generator (insight_generator.py)
- **Role**: Strategic reasoning
- **Action**: Identifies patterns, trends, and actionable insights from analyzed facts
- **Output**: `insights` with strategic recommendations

### 5. 📝 Report Builder (reporter.py)
- **Role**: Final report synthesis
- **Action**: Compiles all information into a structured Markdown report
- **Output**: `final_report` with citations and references

## 💾 State Management (state.py)

The `ResearchState` TypedDict holds all data passed between agents:

```python
class ResearchState(TypedDict):
    user_query:     str
    sub_queries:    List[str]
    routing_plan:   List[SubQueryRoute]
    raw_documents:  List[str]
    analyzed_facts: List[str]
    insights:       List[str]
    final_report:   str
```

## 🏗️ Graph Definition (graph.py)

The graph is built using `langgraph.graph.StateGraph`:

```python
graph_builder = StateGraph(ResearchState)

# Add nodes
graph_builder.add_node("planner", planner_agent)
graph_builder.add_node("retriever", dynamic_retriever)
graph_builder.add_node("analyst", critical_analyst)
graph_builder.add_node("insight_generator", insight_generator)
graph_builder.add_node("reporter", report_builder)

# Define edges
graph_builder.set_entry_point("planner")
graph_builder.add_edge("planner", "retriever")
graph_builder.add_edge("retriever", "analyst")
graph_builder.add_edge("analyst", "insight_generator")
graph_builder.add_edge("insight_generator", "reporter")

# Compile graph
research_graph = graph_builder.compile()
```

## 🚀 How It Works

1. **User submits query** to the Streamlit frontend
2. **Planner agent** decomposes query and creates routing plan
3. **Retriever agent** executes all sub-queries in parallel
4. **Analyst agent** filters and validates information
5. **Insight generator** synthesizes strategic insights
6. **Reporter agent** builds final Markdown report
7. **Report** is displayed in the frontend

## 🛠️ Dependencies

```bash
langgraph
langchain
langchain-community
langchain-core
openai
tavily-python
chromadb
fastembed
python-dotenv
```

## 🧪 Testing

Run the graph directly:

```bash
python core/graph.py
```

Or run the full application:

```bash
streamlit run app.py
```

## 📝 Prompts (prompts.py)

All prompts are centralized in `core/utils/prompts.py` for easy management:

- `PLANNER_PROMPT` - Query decomposition
- `RETRIEVER_PROMPT` - Data retrieval instructions
- `ANALYST_PROMPT` - Fact-checking and validation
- `INSIGHT_PROMPT` - Strategic reasoning
- `REPORTER_PROMPT` - Report synthesis

## 🔄 Customization

To modify agent behavior:

1. Edit the prompt templates in `core/utils/prompts.py`
2. Adjust agent logic in `core/agents/*.py`
3. Update `core/graph.py` to change graph topology
4. Modify `core/state.py` to add/remove state fields

## 📊 Performance

- **Parallel retrieval**: All sub-queries run concurrently for faster data collection
- **State management**: Incremental updates reduce memory usage
- **Local processing**: ChromaDB + FastEmbed = zero cloud cost for retrieval

## 🎯 Key Features

- 🔄 **Multi-agent pipeline** with specialized roles
- 🎯 **Dynamic query decomposition** and routing
- 🔍 **Parallel retrieval** from multiple sources
- 📊 **Fact-checking** and validation
- 🧠 **Strategic reasoning** and insights
- 📝 **Professional report generation** with citations
- 💾 **Local-first architecture** with ChromaDB + FastEmbed
- ⚡ **Optimized for performance** with parallel processing
