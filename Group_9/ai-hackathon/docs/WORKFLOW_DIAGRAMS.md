# AI Hackathon Workflow Diagrams

## End-to-End Research Workflow

```mermaid
flowchart TD
    Start[User opens Research Setup]
    Draft[Draft state saved locally]
    Submit[Start research]
    API[POST /api/research]
    Session[Create ResearchSession]
    Persist[Persist session to SQLite]
    Run[Background research execution]
    Planner[Planner Agent]
    Retriever[Contextual Retriever]
    Analysis[Critical Analysis Agent]
    Contradiction[Contradiction Checker]
    Insight[Insight Generation Agent]
    Reporter[Report Builder Agent]
    QA[QA Review Agent]
    Complete[Session marked complete]
    Output[Research Output page]

    Start --> Draft
    Draft --> Submit
    Submit --> API
    API --> Session
    Session --> Persist
    Persist --> Run
    Run --> Planner
    Planner --> Retriever
    Retriever --> Analysis
    Analysis --> Contradiction
    Contradiction --> Insight
    Insight --> Reporter
    Reporter --> QA
    QA --> Complete
    Complete --> Output
```

## LLM Agent Reasoning Workflow

```mermaid
flowchart LR
    Findings[Retrieved Findings]
    AnalysisLLM[Critical Analysis LLM]
    Claims[Structured Claims]
    ContradictionLLM[Contradiction LLM]
    Contradictions[Structured Contradictions]
    InsightLLM[Insight LLM]
    Insights[Insights, Entities, Relationships]
    QALLM[QA Review LLM]
    QAResult[QA Verdict and Warnings]

    Findings --> AnalysisLLM
    AnalysisLLM --> Claims
    Claims --> ContradictionLLM
    ContradictionLLM --> Contradictions
    Claims --> InsightLLM
    Contradictions --> InsightLLM
    InsightLLM --> Insights
    Claims --> QALLM
    Contradictions --> QALLM
    Insights --> QALLM
    QALLM --> QAResult
```

## Local-First Retrieval Workflow

```mermaid
flowchart TD
    Question[Sub-question]
    LocalFirst[Search Local RAG first]
    LocalIndex[Semantic local index]
    Embed[Sentence Transformers embedding]
    NeedMore{Enough evidence?}
    Web[Tavily web and news retrieval]
    Arxiv[arXiv retrieval]
    Score[Score, dedupe, rank]
    Findings[Normalized findings and sources]

    Question --> LocalFirst
    LocalFirst --> LocalIndex
    LocalIndex --> Embed
    Embed --> NeedMore
    NeedMore -- Yes --> Score
    NeedMore -- No --> Web
    NeedMore -- No --> Arxiv
    Web --> Score
    Arxiv --> Score
    Score --> Findings
```

## Output Hydration Workflow

```mermaid
sequenceDiagram
    participant U as User
    participant Output as Research Output
    participant Store as Zustand Output Store
    participant Cache as Persisted Session Cache
    participant API as FastAPI
    participant SSE as SSE Stream

    U->>Output: Open output route
    Output->>Store: Read UI state
    Output->>Cache: Read cached session snapshot
    Cache-->>Output: Hydrate session immediately
    Output->>API: GET /api/research/{session_id}/state
    API-->>Output: Fresh session payload
    Output->>Store: Persist refreshed output state
    Output->>SSE: Connect to /stream when running
    SSE-->>Output: Live events
    Output->>API: Refresh state on stream events
```

## SSE and Durable Recovery Workflow

```mermaid
flowchart TD
    Start[Active run starts]
    Queue[SSE queue emits live events]
    Persist[Session store persists events and traces]
    Restart{Server restart?}
    Recover[Load persisted session from SQLite]
    Mark[Mark interrupted run as error with recovery note]
    Output[Output page can still restore session]

    Start --> Queue
    Queue --> Persist
    Persist --> Restart
    Restart -- No --> Queue
    Restart -- Yes --> Recover
    Recover --> Mark
    Mark --> Output
```

## Dig Deeper Workflow

```mermaid
flowchart TD
    Select[User selects finding, claim, or insight]
    Request[POST /api/research/{id}/dig-deeper]
    Focus[Create focused follow-up session]
    Run[Run follow-up research pipeline]
    Merge[Merge follow-up sources, claims, insights, and report]
    Persist[Persist merged session]
    Refresh[Refresh Research Output]

    Select --> Request
    Request --> Focus
    Focus --> Run
    Run --> Merge
    Merge --> Persist
    Persist --> Refresh
```

## Frontend Navigation and Persistence Workflow

```mermaid
flowchart LR
    Setup[Research Setup]
    Draft[Local setup draft]
    Start[Start research]
    Output[Research Output]
    UIState[Persisted output UI state]
    SessionCache[Persisted session cache]
    Reopen[Reopen same session later]

    Setup --> Draft
    Draft --> Start
    Start --> Output
    Output --> UIState
    Output --> SessionCache
    Reopen --> UIState
    Reopen --> SessionCache
    UIState --> Output
    SessionCache --> Output
```

## Report Generation Workflow

```mermaid
flowchart TD
    Session[ResearchSession]
    Sources[Ordered sources]
    Claims[Claims]
    Contradictions[Contradictions]
    Insights[Insights]
    Sections[Structured report sections]
    Blocks[Summary-first report blocks]
    Visuals[Optional quantitative visuals]
    Export[Markdown and PDF export]

    Session --> Sources
    Session --> Claims
    Session --> Contradictions
    Session --> Insights
    Sources --> Sections
    Claims --> Sections
    Contradictions --> Sections
    Insights --> Sections
    Sections --> Blocks
    Sections --> Visuals
    Blocks --> Export
    Visuals --> Export
```

## Architecture Notes

- `Research Setup` is the draft and submission workspace.
- `Research Output` is the persistent read and analysis workspace.
- local RAG remains the first retrieval path when enabled.
- reasoning stages are now primarily LLM-backed with fallback behavior.
- sessions are durable in SQLite even though live SSE fanout still uses in-memory queues.
- output hydration now uses both client-side cache and backend restore.
