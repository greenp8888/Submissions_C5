# FinanceDoctor Workflow Diagrams

## Purpose

This document captures the implemented workflows for document upload and ingestion, RAG pipeline processing, multi-agent query execution, dashboard rendering, data exploration, and provider configuration.

## First-Launch Setup Workflow

```mermaid
flowchart TD
    Open[User opens app at localhost:8501]
    Sidebar[Sidebar loads]
    Keys{API keys entered?}
    EnterKeys[Enter OpenRouter + Tavily keys]
    SelectModel[Select LLM model]
    BuildGraph["build_graph() creates LangGraph"]
    Ready[AI Graph ready — 5 nodes, 4 agents]
    Upload[Upload financial documents]
    Process["Click 🚀 Process Documents"]
    Ingest[Parse + chunk + embed + store]
    Active[System fully active]

    Open --> Sidebar
    Sidebar --> Keys
    Keys -- No --> EnterKeys
    Keys -- Yes --> SelectModel
    EnterKeys --> SelectModel
    SelectModel --> BuildGraph
    BuildGraph --> Ready
    Ready --> Upload
    Upload --> Process
    Process --> Ingest
    Ingest --> Active
```

## Document Upload and Ingestion Workflow

```mermaid
flowchart TD
    Upload[User uploads files via sidebar]
    Filter{New files only?}
    Skip[Skip already processed files]
    Parse["parse_document() dispatch"]

    CSV{Is CSV?}
    CSVEnc[Try 5 encodings sequentially]
    CSVResult["Return (markdown, DataFrame)"]

    Excel{Is Excel?}
    ExcelSheets[Read all sheets via openpyxl]
    ExcelConcat[Concatenate DataFrames]
    ExcelResult["Return (markdown, combined DataFrame)"]

    PDF{Is PDF?}
    HasLlama{LlamaParse key?}
    LlamaParse[LlamaParse cloud API]
    LlamaOK{Parse success?}
    PyPDF2[PyPDF2 local fallback]
    TableExtract[Try extract table from text]
    PDFResult["Return (text, optional DataFrame)"]

    AppendText[Append text to financial_data_md]
    AppendDF[Concat DataFrame to financial_df]

    RAGInit{RAG pipeline initialized?}
    CreateRAG[Create RAGPipeline instance]
    Chunk[Chunk text with RecursiveCharacterTextSplitter]
    Embed[Batch encode with SentenceTransformer]
    Store[Append to LanceDB table]
    UpdateCount[Update chunk_count]
    MarkProcessed[Add filename to processed_files]
    RebuildGraph[Rebuild LangGraph with RAG pipeline]
    Done[Rerun Streamlit — data ingested]

    Upload --> Filter
    Filter -- Already processed --> Skip
    Filter -- New files --> Parse

    Parse --> CSV
    Parse --> Excel
    Parse --> PDF

    CSV --> CSVEnc --> CSVResult
    Excel --> ExcelSheets --> ExcelConcat --> ExcelResult
    PDF --> HasLlama
    HasLlama -- Yes --> LlamaParse --> LlamaOK
    HasLlama -- No --> PyPDF2
    LlamaOK -- Yes --> TableExtract
    LlamaOK -- No --> PyPDF2
    PyPDF2 --> TableExtract --> PDFResult

    CSVResult --> AppendText
    ExcelResult --> AppendText
    PDFResult --> AppendText
    AppendText --> AppendDF

    AppendDF --> RAGInit
    RAGInit -- No --> CreateRAG --> Chunk
    RAGInit -- Yes --> Chunk
    Chunk --> Embed --> Store --> UpdateCount --> MarkProcessed
    MarkProcessed --> RebuildGraph --> Done
```

## RAG Ingest Workflow

```mermaid
flowchart LR
    Text[Document text]
    Split["RecursiveCharacterTextSplitter (500 chars, 50 overlap)"]
    Chunks["List of text chunks"]
    Encode["SentenceTransformer.encode() batch"]
    Vectors["384-dim embedding vectors"]
    Table{LanceDB table exists?}
    Create["db.create_table('financial_docs')"]
    Append["table.add(data)"]
    Ready[RAGPipeline.is_ready = True]

    Text --> Split
    Split --> Chunks
    Chunks --> Encode
    Encode --> Vectors
    Vectors --> Table
    Table -- No --> Create --> Ready
    Table -- Yes --> Append --> Ready
```

## RAG Query Workflow

```mermaid
flowchart LR
    Question[User query or agent tool call]
    Encode["SentenceTransformer.encode()"]
    QueryVec[384-dim query vector]
    Search["LanceDB .search(vector).limit(top_k)"]
    Results[Top-k text chunks]
    Agent[Return to calling agent]

    Question --> Encode
    Encode --> QueryVec
    QueryVec --> Search
    Search --> Results
    Results --> Agent
```

## End-to-End Chat Query Workflow

```mermaid
flowchart TD
    UserInput["User types question in Chat tab"]
    AddMessage[Append HumanMessage to session state]
    BuildHistory[Build LangChain message history]
    TruncateData[Truncate financial_data_md to 3000 chars]
    Invoke["graph.invoke(state)"]

    Orchestrator[Orchestrator Node]
    LLMClassify[LLM classifies query intent]
    Normalize[Keyword normalization safety net]
    Route{Route decision}

    Debt[Debt Analyzer ReAct Agent]
    Savings[Savings Strategy ReAct Agent]
    Budget[Budget Advisor ReAct Agent]
    Action[Action Planner ReAct Agent]

    InjectPrompt[Inject system prompt + financial data block]
    RAGTool["Tool: search_financial_data"]
    TavilyTool["Tool: tavily_search"]
    AgentResponse[Extract final AIMessage]

    Display[Display response with route badge]
    SaveHistory[Append to session messages]

    UserInput --> AddMessage
    AddMessage --> BuildHistory
    BuildHistory --> TruncateData
    TruncateData --> Invoke

    Invoke --> Orchestrator
    Orchestrator --> LLMClassify
    LLMClassify --> Normalize
    Normalize --> Route

    Route -->|"debt_analyzer"| Debt
    Route -->|"savings_strategy"| Savings
    Route -->|"budget_advisor"| Budget
    Route -->|"action_planner"| Action

    Debt --> InjectPrompt
    Savings --> InjectPrompt
    Budget --> InjectPrompt
    Action --> InjectPrompt

    InjectPrompt --> RAGTool
    InjectPrompt --> TavilyTool
    RAGTool --> AgentResponse
    TavilyTool --> AgentResponse

    AgentResponse --> Display
    Display --> SaveHistory
```

## Orchestrator Routing Workflow

```mermaid
flowchart TD
    Query[Latest user message]
    SystemPrompt[ORCHESTRATOR_SYSTEM_PROMPT]
    LLM["LLM.invoke([system, user])"]
    RawOutput[Raw LLM response]
    Parse[Strip and lowercase]
    
    HasDebt{"Contains 'debt'?"}
    HasSaving{"Contains 'saving' or 'invest'?"}
    HasAction{"Contains 'action' or 'plan' or 'step' or 'priorit'?"}
    Default["Default: budget_advisor"]

    DebtRoute["route: debt_analyzer"]
    SavingsRoute["route: savings_strategy"]
    ActionRoute["route: action_planner"]
    BudgetRoute["route: budget_advisor"]

    Query --> SystemPrompt
    SystemPrompt --> LLM
    LLM --> RawOutput
    RawOutput --> Parse
    Parse --> HasDebt
    HasDebt -- Yes --> DebtRoute
    HasDebt -- No --> HasSaving
    HasSaving -- Yes --> SavingsRoute
    HasSaving -- No --> HasAction
    HasAction -- Yes --> ActionRoute
    HasAction -- No --> Default
    Default --> BudgetRoute
```

## Specialist Agent Execution Workflow

```mermaid
flowchart LR
    State[FinanceDoctorState]
    DataBlock["_build_data_block(state)"]
    SystemPrompt["Agent system prompt + INDIAN_FINANCE_RULES + data block"]
    Messages["[SystemMessage] + state.messages"]
    ReAct["create_react_agent.invoke()"]
    
    ToolLoop{Agent needs tool?}
    RAG["search_financial_data → LanceDB"]
    Web["tavily_search → Tavily API"]
    ToolResult[Tool returns result]
    
    FinalMsg[Extract last AIMessage without tool_calls]
    Return["Return {messages: [final]}"]

    State --> DataBlock
    DataBlock --> SystemPrompt
    SystemPrompt --> Messages
    Messages --> ReAct
    ReAct --> ToolLoop
    ToolLoop -- Yes --> RAG
    ToolLoop -- Yes --> Web
    RAG --> ToolResult --> ReAct
    Web --> ToolResult
    ReAct --> FinalMsg
    FinalMsg --> Return
```

## Dashboard Rendering Workflow

```mermaid
flowchart TD
    Open[User opens Dashboard tab]
    HasData{financial_df in session state?}
    EmptyState[Show 'No Data Yet' placeholder]
    DetectCols["detect_columns(df)"]
    ColMap["Column mapping: date, amount, category, type, description, balance"]

    Cards["render_summary_cards() — Income, Expenses, Savings, Rate"]
    TwoCol[Two-column layout]
    Spending["render_spending_breakdown() — Donut chart"]
    Savings["render_savings_tracker() — Pie + Bar"]
    Trends["render_monthly_trends() — Grouped bar + line"]
    TwoCol2[Two-column layout]
    DebtChart["render_debt_analysis() — Horizontal bar"]
    TopExp["render_top_expenses() — Data table"]

    Open --> HasData
    HasData -- No --> EmptyState
    HasData -- Yes --> DetectCols
    DetectCols --> ColMap
    ColMap --> Cards
    Cards --> TwoCol
    TwoCol --> Spending
    TwoCol --> Savings
    Savings --> Trends
    Spending --> Trends
    Trends --> TwoCol2
    TwoCol2 --> DebtChart
    TwoCol2 --> TopExp
```

## Data Explorer Workflow

```mermaid
flowchart TD
    Open[User opens Data Explorer tab]
    HasData{financial_df in session state?}
    EmptyState[Show 'No Data Loaded' placeholder]
    ShowMeta["Show row count, column count, source"]
    ColSummary[Column Summary expander]
    DetectCols["detect_columns(df)"]
    Filters[Category and Type filter dropdowns]
    ApplyFilter[Apply filters to DataFrame]
    ShowTable["st.dataframe() with filtered data"]
    Download["Download Filtered Data (CSV)"]

    RAGInfo{Data ingested?}
    VectorInfo[Show LanceDB chunk count and model info]
    TestSearch[RAG test search input]
    SearchResults[Display matching chunks]

    Open --> HasData
    HasData -- No --> EmptyState
    HasData -- Yes --> ShowMeta
    ShowMeta --> ColSummary
    ColSummary --> DetectCols
    DetectCols --> Filters
    Filters --> ApplyFilter
    ApplyFilter --> ShowTable
    ShowTable --> Download
    Download --> RAGInfo
    RAGInfo -- Yes --> VectorInfo
    VectorInfo --> TestSearch
    TestSearch --> SearchResults
    RAGInfo -- No --> TestSearch
```

## Model Change Workflow

```mermaid
flowchart TD
    Select[User selects new model from dropdown]
    Compare{Current model != selected model?}
    NoChange[Keep existing graph]
    Rebuild["build_graph(api_key, tavily_key, new_model, rag_pipeline)"]
    NewLLM[Create new ChatOpenAI instance]
    NewAgents[Create 4 new ReAct agents]
    NewGraph[Compile new StateGraph]
    Update["session_state.current_model = new_model"]
    Ready[AI Graph ready with new model]

    Select --> Compare
    Compare -- No --> NoChange
    Compare -- Yes --> Rebuild
    Rebuild --> NewLLM
    NewLLM --> NewAgents
    NewAgents --> NewGraph
    NewGraph --> Update
    Update --> Ready
```

## Clear Data Workflow

```mermaid
flowchart TD
    Click["User clicks 🗑️ Clear Data"]
    RAG{RAG pipeline exists?}
    DropTable["rag_pipeline.clear() — drop LanceDB table"]
    ResetState[Reset all session state fields]
    ClearMD["financial_data_md = ''"]
    ClearDF["financial_df = None"]
    ClearGraph["graph = None"]
    ClearRAG["rag_pipeline = None"]
    ClearFiles["processed_files = set()"]
    ClearChunks["chunk_count = 0"]
    Rerun["st.rerun()"]

    Click --> RAG
    RAG -- Yes --> DropTable --> ResetState
    RAG -- No --> ResetState
    ResetState --> ClearMD
    ResetState --> ClearDF
    ResetState --> ClearGraph
    ResetState --> ClearRAG
    ResetState --> ClearFiles
    ResetState --> ClearChunks
    ClearChunks --> Rerun
```

## Error Handling Workflow

```mermaid
flowchart TD
    Action[Any user action]

    ParseError{Document parse error?}
    ParseMsg["st.error('Parsing failed for {file}: {error}')"]
    Continue[Continue to next file]

    RAGError{RAG pipeline error?}
    RAGMsg["st.error('RAG pipeline error for {file}: {error}')"]

    NoGraph{Graph not built?}
    NoGraphMsg["st.error('Please enter your API keys')"]
    Stop["st.stop()"]

    ChatError{Chat invocation error?}
    ChatMsg["st.error('Error: {message}')"]
    SaveError[Save error message to chat history]

    NoKeys{Missing API keys?}
    Warning["st.warning('Enter OpenRouter + Tavily keys')"]

    Action --> ParseError
    ParseError -- Yes --> ParseMsg --> Continue
    ParseError -- No --> RAGError
    RAGError -- Yes --> RAGMsg --> Continue
    RAGError -- No --> NoGraph
    NoGraph -- Yes --> NoGraphMsg --> Stop
    NoGraph -- No --> ChatError
    ChatError -- Yes --> ChatMsg --> SaveError
    ChatError -- No --> NoKeys
    NoKeys -- Yes --> Warning
```

## Notes

- `Chat` tab is the primary conversational workspace with RAG-grounded AI responses.
- `Dashboard` tab is the interactive visualization workspace powered by auto-detected column roles.
- `Data Explorer` tab is the tabular inspection and export workspace with RAG test search.
- document parsing uses fallback chains for maximum file compatibility.
- LlamaParse is the primary PDF parser; PyPDF2 is always available as a local fallback.
- the Orchestrator uses LLM classification with keyword normalization for robust routing.
- all specialist agents receive shared Indian financial context via `INDIAN_FINANCE_RULES`.
- RAG retrieval is local-first via LanceDB — no cloud vector database dependency.
- session state is Streamlit-managed and does not persist across server restarts.
