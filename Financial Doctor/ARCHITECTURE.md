# FinanceDoctor Architecture

## Purpose

This document describes the implemented architecture of `FinanceDoctor` as it exists in code today. It focuses on the real system shape:

- Streamlit dashboard with three product tabs (Chat, Dashboard, Data Explorer)
- 4-layer architecture (Document Ingestion → RAG Pipeline → LangGraph Orchestration → UI)
- LangGraph-based multi-agent orchestration with conditional routing
- LLM-backed specialist ReAct agents with tool use
- local semantic retrieval via LanceDB
- multi-format document parsing with fallback chains
- Streamlit session state management

## System Overview

```mermaid
flowchart TB
    User[User]

    subgraph UI["Streamlit Dashboard (Layer 4)"]
        Sidebar[Sidebar Configuration]
        ChatTab[Chat Tab]
        DashTab[Dashboard Tab]
        DataTab[Data Explorer Tab]
        SessionState[st.session_state]
        CSS[Custom CSS Theme]
    end

    subgraph Orchestration["LangGraph Orchestration (Layer 3)"]
        Orchestrator[Orchestrator Node]
        DebtAgent[Debt Analyzer ReAct Agent]
        SavingsAgent[Savings Strategy ReAct Agent]
        BudgetAgent[Budget Advisor ReAct Agent]
        ActionAgent[Action Planner ReAct Agent]
        State[FinanceDoctorState TypedDict]
    end

    subgraph RAG["RAG Pipeline (Layer 2)"]
        TextSplitter[RecursiveCharacterTextSplitter]
        EmbedModel["SentenceTransformer (all-MiniLM-L6-v2)"]
        LanceDB[LanceDB Vector Store]
        QueryEngine[Vector Search Engine]
    end

    subgraph Ingestion["Document Ingestion (Layer 1)"]
        CSVParser[CSV Parser — Multi-Encoding]
        ExcelParser[Excel Parser — Multi-Sheet]
        PDFLlama[LlamaParse — Primary]
        PDFPyPDF2[PyPDF2 — Fallback]
        TableExtractor[PDF Table Extractor]
    end

    subgraph Providers[External Providers]
        OpenRouter[OpenRouter API]
        Tavily[Tavily Search API]
        LlamaCloud[LlamaIndex Cloud]
    end

    User --> Sidebar
    User --> ChatTab
    User --> DashTab
    User --> DataTab

    Sidebar --> SessionState
    ChatTab --> SessionState
    SessionState --> Orchestrator

    Orchestrator --> DebtAgent
    Orchestrator --> SavingsAgent
    Orchestrator --> BudgetAgent
    Orchestrator --> ActionAgent

    DebtAgent --> QueryEngine
    SavingsAgent --> QueryEngine
    BudgetAgent --> QueryEngine
    ActionAgent --> QueryEngine

    DebtAgent --> Tavily
    SavingsAgent --> Tavily
    BudgetAgent --> Tavily
    ActionAgent --> Tavily

    Sidebar --> CSVParser
    Sidebar --> ExcelParser
    Sidebar --> PDFLlama
    PDFLlama --> PDFPyPDF2
    PDFPyPDF2 --> TableExtractor

    CSVParser --> TextSplitter
    ExcelParser --> TextSplitter
    PDFLlama --> TextSplitter
    PDFPyPDF2 --> TextSplitter
    TextSplitter --> EmbedModel
    EmbedModel --> LanceDB
    QueryEngine --> LanceDB

    Orchestrator --> OpenRouter
    DebtAgent --> OpenRouter
    SavingsAgent --> OpenRouter
    BudgetAgent --> OpenRouter
    ActionAgent --> OpenRouter
    PDFLlama --> LlamaCloud

    SessionState --> DashTab
    SessionState --> DataTab
```

## Layer 1 — Document Ingestion Architecture

### File: `document_parser.py`

### Parser Flow

```mermaid
flowchart TD
    Upload[User uploads file]
    Detect{File extension?}

    CSV[CSV Parser]
    CSVEnc{Try encodings}
    UTF8["utf-8"]
    UTF8BOM["utf-8-sig"]
    UTF16["utf-16"]
    Latin1["latin-1"]
    CP1252["cp1252"]
    CSVResult["(markdown_text, DataFrame)"]

    Excel[Excel Parser]
    Sheets[Read all sheets via openpyxl]
    Combine[Concatenate DataFrames]
    ExcelResult["(markdown_text, combined DataFrame)"]

    PDF[PDF Parser]
    HasLlama{LlamaParse key provided?}
    LlamaParse[LlamaParse Cloud API]
    LlamaOK{Parse success?}
    PyPDF2[PyPDF2 Fallback]
    TableDetect[Try extract table from text]
    HasTable{Tabular structure found?}
    PDFResult["(text, optional DataFrame)"]

    Upload --> Detect
    Detect -- .csv --> CSV
    Detect -- .xlsx / .xls --> Excel
    Detect -- .pdf --> PDF

    CSV --> CSVEnc
    CSVEnc --> UTF8
    CSVEnc --> UTF8BOM
    CSVEnc --> UTF16
    CSVEnc --> Latin1
    CSVEnc --> CP1252
    UTF8 --> CSVResult
    UTF8BOM --> CSVResult
    UTF16 --> CSVResult
    Latin1 --> CSVResult
    CP1252 --> CSVResult

    Excel --> Sheets
    Sheets --> Combine
    Combine --> ExcelResult

    PDF --> HasLlama
    HasLlama -- Yes --> LlamaParse
    HasLlama -- No --> PyPDF2
    LlamaParse --> LlamaOK
    LlamaOK -- Yes --> TableDetect
    LlamaOK -- No --> PyPDF2
    PyPDF2 --> TableDetect
    TableDetect --> HasTable
    HasTable -- Yes --> PDFResult
    HasTable -- No --> PDFResult
```

### Parser Responsibilities

- `parse_csv()` reads CSV files through a waterfall of 5 encodings, returning a markdown table and a DataFrame.
- `parse_excel()` reads all sheets from an Excel workbook, concatenates them into a single DataFrame, and produces per-sheet markdown.
- `parse_pdf_llamaparse()` uses the LlamaParse cloud API to convert PDFs to high-quality markdown. Requires a valid API key.
- `parse_pdf_pypdf2()` uses PyPDF2 as a local fallback, extracting page-by-page text with page number annotations.
- `_try_extract_table_from_text()` attempts best-effort tabular extraction from PDF text by detecting CSV-like or TSV-like line patterns.
- `parse_document()` is the main entry point that dispatches to the correct parser based on file extension.

## Layer 2 — RAG Pipeline Architecture

### File: `rag_pipeline.py`

### Pipeline Flow

```mermaid
flowchart LR
    Text[Parsed document text]
    Chunk[RecursiveCharacterTextSplitter]
    Embed["SentenceTransformer.encode()"]
    Store[LanceDB table: financial_docs]
    Query[User query]
    QEmbed["SentenceTransformer.encode()"]
    Search["LanceDB .search().limit(top_k)"]
    Results[Top-k text chunks]

    Text --> Chunk
    Chunk --> Embed
    Embed --> Store
    Query --> QEmbed
    QEmbed --> Search
    Search --> Store
    Store --> Results
```

### RAG Configuration

| Parameter | Value | Source |
| --- | --- | --- |
| Embedding model | `all-MiniLM-L6-v2` | `config.py` |
| Embedding dimension | 384 | `config.py` |
| Chunk size | 500 characters | `config.py` |
| Chunk overlap | 50 characters | `config.py` |
| LanceDB path | `./lancedb_data` | `config.py` |
| LanceDB table | `financial_docs` | `config.py` |
| Default top_k | 5 | `rag_pipeline.py` |

### RAGPipeline Class Responsibilities

- `__init__()` configures the text splitter and sets up lazy loaders for the embedding model and database connection.
- `ingest()` chunks text, batch-encodes embeddings, and appends to (or creates) the LanceDB table. Returns the number of chunks stored.
- `query()` encodes the question and performs a vector search, returning the top-k most relevant text chunks.
- `is_ready` property indicates whether any data has been ingested.
- `chunk_count` property returns the current number of rows in the vector table.
- `clear()` drops the LanceDB table and resets all state.

## Layer 3 — LangGraph Orchestration Architecture

### File: `graph.py` and `config.py`

### Graph Topology

```mermaid
flowchart LR
    START([START])
    Orchestrator[Orchestrator Node]
    Debt[Debt Analyzer]
    Savings[Savings Strategy]
    Budget[Budget Advisor]
    Action[Action Planner]
    END_NODE([END])

    START --> Orchestrator
    Orchestrator -->|"debt_analyzer"| Debt
    Orchestrator -->|"savings_strategy"| Savings
    Orchestrator -->|"budget_advisor"| Budget
    Orchestrator -->|"action_planner"| Action
    Debt --> END_NODE
    Savings --> END_NODE
    Budget --> END_NODE
    Action --> END_NODE
```

### State Schema

```mermaid
classDiagram
    class FinanceDoctorState {
        +list~BaseMessage~ messages
        +str financial_data_summary
        +str route_decision
    }
```

The `messages` field uses `operator.add` as its reducer, enabling message accumulation across nodes.

### Node Roles

- **Orchestrator Node**
  Receives the latest user message, invokes the LLM with `ORCHESTRATOR_SYSTEM_PROMPT`, and parses the response into one of four route decisions. Uses keyword normalization as a safety net when LLM output is not an exact match.

- **Debt Analyzer Node**
  A ReAct agent specialized in debt management: DTI ratio analysis, payoff timeline comparison (Avalanche vs Snowball), interest rate optimization, debt consolidation, and credit card prioritization.

- **Savings Strategy Node**
  A ReAct agent specialized in savings and investments: emergency fund sizing, goal-based savings, investment comparison (PPF, FD, SIP, NPS, ELSS), tax-saving under 80C/80D/24b, insurance planning, and retirement corpus estimation.

- **Budget Advisor Node**
  A ReAct agent specialized in budgeting: category-wise spending analysis, 50/30/20 rule, expense optimization, monthly category limits, spending trend identification, and Indian household benchmarks.

- **Action Planner Node**
  A ReAct agent specialized in executable plans: prioritized step-by-step actions, time-bound breakdowns (This Week / This Month / This Quarter), quick wins, habit formation, milestones, and risk mitigation.

### Tool Configuration

Each specialist ReAct agent is equipped with two tools:

| Tool | Name | Description |
| --- | --- | --- |
| RAG Search | `search_financial_data` | Searches the user's uploaded financial documents via LanceDB vector retrieval |
| Web Search | `tavily_search` | Performs live web search for current financial rates and data, scoped to finance topics |

### LLM Configuration

```mermaid
flowchart LR
    OpenRouter[OpenRouter API Base]
    LLM[ChatOpenAI]
    Agents[All 5 Nodes]

    LLM --> OpenRouter
    Agents --> LLM
```

All nodes share a single `ChatOpenAI` instance configured with:

- `openai_api_base`: `https://openrouter.ai/api/v1`
- `temperature`: 0.3
- `max_tokens`: 4096

### System Prompt Architecture

Each specialist agent receives a composed system prompt:

```
[Agent-specific system prompt]
  + [INDIAN_FINANCE_RULES shared block]
  + [Financial data block from state]
```

The `INDIAN_FINANCE_RULES` block is injected into every specialist prompt, ensuring consistent Indian financial context across all agents.

## Layer 4 — Streamlit Dashboard Architecture

### Files: `app.py` and `dashboard.py`

### Tab Structure

```mermaid
flowchart LR
    App[app.py]
    Chat["💬 Chat"]
    Dashboard["📊 Dashboard"]
    DataExplorer["📁 Data Explorer"]

    App --> Chat
    App --> Dashboard
    App --> DataExplorer
```

### Dashboard Responsibilities

- `app.py` provides the full Streamlit application shell: page config, custom CSS, sidebar, session state initialization, and three-tab layout.
- `dashboard.py` provides Plotly-based visualization functions with a consistent dark theme and color palette.

### Dashboard Visualization Components

| Function | Visual | Purpose |
| --- | --- | --- |
| `render_summary_cards()` | Metric cards | Total Income, Expenses, Net Savings, Savings Rate |
| `render_spending_breakdown()` | Donut chart | Category-wise expense breakdown (excludes investments/EMI) |
| `render_monthly_trends()` | Grouped bar + line | Monthly Income vs Expenses with Net Savings overlay |
| `render_debt_analysis()` | Horizontal bar | Debt/EMI breakdown by source with monthly obligation |
| `render_savings_tracker()` | Pie + bar | Investment allocation and monthly investment trends |
| `render_top_expenses()` | Data table | Top N largest debit transactions |
| `detect_columns()` | — | Auto-detects column roles (date, amount, category, type, description, balance) |

### Column Detection

The `detect_columns()` function auto-maps DataFrame columns by scanning column names for keywords:

```mermaid
flowchart TD
    DF[DataFrame columns]
    Scan{Scan column names}
    Date["date / time / period → date"]
    Amount["amount / value / sum → amount"]
    Category["category / categ / head → category"]
    Type["type / cr/dr / direction → type"]
    Desc["desc / narr / particular → description"]
    Balance["balance / bal / closing → balance"]
    Split{Split credit/debit columns?}
    Merge["Merge into _Parsed_Amount + _Parsed_Type"]

    DF --> Scan
    Scan --> Date
    Scan --> Amount
    Scan --> Category
    Scan --> Type
    Scan --> Desc
    Scan --> Balance
    Amount --> Split
    Type --> Split
    Split -- Yes --> Merge
```

### Session State Schema

```mermaid
classDiagram
    class SessionState {
        +list messages
        +str financial_data_md
        +DataFrame financial_df
        +CompiledGraph graph
        +RAGPipeline rag_pipeline
        +str current_model
        +bool data_ingested
        +int chunk_count
        +str doc_source
        +set processed_files
    }
```

## Provider Architecture

### Runtime Configuration

```mermaid
flowchart LR
    Sidebar[Streamlit Sidebar]
    SessionState[st.session_state]
    BuildGraph["build_graph()"]
    LLM[ChatOpenAI via OpenRouter]
    TavilyTool[TavilySearch Tool]
    RAGTool[RAG Search Tool]
    Agents[ReAct Agents]

    Sidebar --> SessionState
    SessionState --> BuildGraph
    BuildGraph --> LLM
    BuildGraph --> TavilyTool
    BuildGraph --> RAGTool
    LLM --> Agents
    TavilyTool --> Agents
    RAGTool --> Agents
```

Important behavior:

- API keys are entered from the Streamlit sidebar text inputs
- keys are held in Streamlit session state during the runtime session
- the LangGraph is rebuilt whenever the model selection changes
- the Tavily API key is set as an environment variable at graph build time
- keys are never persisted to disk, logged, or returned in responses

## Data Flow Architecture

### End-to-End Data Flow

```mermaid
flowchart TD
    Upload[File Upload via Sidebar]
    Parse["parse_document() — Layer 1"]
    Text[Raw text output]
    DF[Structured DataFrame]
    Chunk["RAGPipeline.ingest() — Layer 2"]
    VectorStore[LanceDB Vector Store]
    SessionMD[session_state.financial_data_md]
    SessionDF[session_state.financial_df]
    Chat[User asks question]
    Orchestrate["graph.invoke() — Layer 3"]
    Route[Route to specialist agent]
    RAGSearch[Agent calls search_financial_data]
    WebSearch[Agent calls tavily_search]
    Response[Agent generates response]
    Display["st.chat_message() — Layer 4"]
    Dashboard["Plotly charts — Layer 4"]

    Upload --> Parse
    Parse --> Text
    Parse --> DF
    Text --> Chunk
    Chunk --> VectorStore
    Text --> SessionMD
    DF --> SessionDF
    Chat --> Orchestrate
    SessionMD --> Orchestrate
    Orchestrate --> Route
    Route --> RAGSearch
    Route --> WebSearch
    RAGSearch --> VectorStore
    Response --> Display
    SessionDF --> Dashboard
```

## Key Implementation Notes

- the system uses a 4-layer architecture: Ingestion → RAG → Orchestration → UI
- all LLM reasoning goes through OpenRouter, allowing model switching without code changes
- RAG retrieval is local-first via LanceDB; no cloud vector database dependency
- document parsing uses a fallback chain (LlamaParse → PyPDF2) for maximum compatibility
- the Orchestrator uses LLM classification followed by keyword normalization for robust routing
- all specialist agents share the same Indian financial context via `INDIAN_FINANCE_RULES`
- dashboard visualizations auto-detect column roles, supporting varied document schemas
- session state is Streamlit-managed; there is no persistent database for sessions

For end-to-end run flows, see [WORKFLOW_DIAGRAMS.md](./WORKFLOW_DIAGRAMS.md).
