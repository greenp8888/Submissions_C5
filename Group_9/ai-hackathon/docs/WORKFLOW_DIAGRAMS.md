# AI Hackathon Workflow Diagrams

## End-to-End Research Workflow

```mermaid
flowchart TD
    Start[User opens Research Setup]
    Draft[Draft state saved locally]
    Submit[Start research]
    API[POST /api/research]
    Session[Create ResearchSession]
    Run[Background research execution]
    Planner[Planner Agent]
    Retriever[Contextual Retriever Agent]
    Analysis[Critical Analysis Agent]
    Insight[Insight Generation Agent]
    Reporter[Report Builder Agent]
    QA[QA Review Agent]
    Complete[Session marked complete]
    Output[Research Output page]

    Start --> Draft
    Draft --> Submit
    Submit --> API
    API --> Session
    Session --> Run
    Run --> Planner
    Planner --> Retriever
    Retriever --> Analysis
    Analysis --> Insight
    Insight --> Reporter
    Reporter --> QA
    QA --> Complete
    Complete --> Output
```

## Retrieval Workflow

```mermaid
flowchart TD
    Question[Sub-question]
    LocalFirst[Check Local RAG first]
    LocalDocs[Local collections and uploaded docs]
    PDFFallback[PDF fallback retrieval]
    NeedMore{Enough evidence?}
    Web[Tavily web/news retrieval]
    Arxiv[arXiv retrieval]
    Expansion[Expansion retrievers]
    Score[Score, dedupe, rank]
    Findings[Normalized findings and sources]

    Question --> LocalFirst
    LocalFirst --> LocalDocs
    LocalFirst --> PDFFallback
    LocalDocs --> NeedMore
    PDFFallback --> NeedMore
    NeedMore -- No --> Web
    NeedMore -- No --> Arxiv
    NeedMore -- No --> Expansion
    NeedMore -- Yes --> Score
    Web --> Score
    Arxiv --> Score
    Expansion --> Score
    Score --> Findings
```

## Session State Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Pending
    Pending --> Running: start_background_research
    Running --> Complete: graph + QA succeed
    Running --> Error: exception
    Complete --> Running: dig deeper follow-up session
    Error --> [*]
    Complete --> [*]
```

## Report Generation Workflow

```mermaid
flowchart TD
    Session[ResearchSession]
    Sources[Ordered sources]
    Claims[Claims and contradictions]
    Insights[Insights and follow-ups]
    Sections[Structured report sections]
    Blocks[Summary-first report blocks]
    Visuals[Optional quantitative visuals]
    Render[Markdown and PDF render services]

    Session --> Sources
    Session --> Claims
    Session --> Insights
    Sources --> Sections
    Claims --> Sections
    Insights --> Sections
    Sections --> Blocks
    Sections --> Visuals
    Blocks --> Render
    Visuals --> Render
```

## Frontend Interaction Workflow

```mermaid
sequenceDiagram
    participant U as User
    participant Setup as Research Setup
    participant API as FastAPI
    participant Coord as Coordinator
    participant Store as Session Store
    participant Output as Research Output

    U->>Setup: Enter question and options
    Setup->>Setup: Persist draft locally
    U->>Setup: Start research
    Setup->>API: POST /api/research
    API->>Coord: Create session and background task
    Coord->>Store: Save session
    API-->>Setup: session_id
    Setup->>Output: Navigate to /research/output/{session_id}
    Output->>API: GET /api/research/{session_id}/state
    Output->>API: GET /api/research/{session_id}/stream
    Coord->>Store: Emit events and traces
    API-->>Output: State + SSE events
    Output->>U: Show progress, report, references, graph, trace
```

## Agent Workflow Diagram

```mermaid
flowchart LR
    Planner[Planner]
    Retriever[Retriever]
    Analysis[Critical Analysis]
    Contradiction[Contradiction Checker]
    Insight[Insight Generation]
    Reporter[Report Builder]
    QA[QA Review]

    Planner --> Retriever
    Retriever --> Analysis
    Analysis --> Contradiction
    Contradiction --> Insight
    Insight --> Reporter
    Reporter --> QA
```

## Architecture Notes

- `Research Setup` is the draft/edit route.
- `Research Output` is the read/analyze route.
- session restore and live progress both depend on `ResearchSession` stored in memory by the backend.
- local RAG is always the first retrieval path when enabled.
- report sections are now structured for presentation, not just markdown strings.
