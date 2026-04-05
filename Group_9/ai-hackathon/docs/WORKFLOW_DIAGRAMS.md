# AI Hackathon Workflow Diagrams

## Purpose

This document captures the implemented workflows for setup, provider initialization, research execution, output hydration, dig deeper continuation, and documentation access.

## First-Launch Provider Setup Workflow

```mermaid
flowchart TD
    Open[User opens app]
    Shell[AppShell boot]
    Cache{Cached provider keys exist?}
    Sync[Sync cached keys to backend runtime]
    Settings[Open Settings page]
    Enter[Enter OpenRouter and Tavily keys]
    Save[Save to browser cache and runtime]
    Runtime[Providers available for current runtime]

    Open --> Shell
    Shell --> Cache
    Cache -- Yes --> Sync
    Cache -- No --> Settings
    Settings --> Enter
    Enter --> Save
    Save --> Runtime
    Sync --> Runtime
```

## End-to-End Research Workflow

```mermaid
flowchart TD
    Setup[Research Setup page]
    Draft[Persist unsaved draft locally]
    Submit[Submit research request]
    API["POST /api/research"]
    Session[Create ResearchSession]
    Persist[Persist session to SQLite]
    Background[Start background run]
    Planner[Planner Agent]
    Retriever[Contextual Retriever]
    Analysis[Critical Analysis Agent]
    Contradiction[Contradiction Checker]
    Insight[Insight Generation Agent]
    Reporter[Report Builder Agent]
    QA[QA Review Agent]
    SaveFinal[Persist completed session]
    Output[Research Output page]

    Setup --> Draft
    Draft --> Submit
    Submit --> API
    API --> Session
    Session --> Persist
    Persist --> Background
    Background --> Planner
    Planner --> Retriever
    Retriever --> Analysis
    Analysis --> Contradiction
    Contradiction --> Insight
    Insight --> Reporter
    Reporter --> QA
    QA --> SaveFinal
    SaveFinal --> Output
```

## LLM Reasoning Workflow

```mermaid
flowchart LR
    Query[Research query]
    Plan[Planner LLM]
    Findings[Retrieved findings]
    AnalysisLLM[Critical Analysis LLM]
    Claims[Claims and evidence summaries]
    ContradictionLLM[Contradiction LLM]
    Disagreement[Contradictions and consensus]
    InsightLLM[Insight LLM]
    Insights[Insights, entities, relationships]
    QALLM[QA Review LLM]
    QAResult[Warnings and completeness checks]

    Query --> Plan
    Plan --> Findings
    Findings --> AnalysisLLM
    AnalysisLLM --> Claims
    Claims --> ContradictionLLM
    ContradictionLLM --> Disagreement
    Claims --> InsightLLM
    Disagreement --> InsightLLM
    InsightLLM --> Insights
    Claims --> QALLM
    Disagreement --> QALLM
    Insights --> QALLM
    QALLM --> QAResult
```

## Local-First Retrieval Workflow

```mermaid
flowchart TD
    SubQuestion[Sub-question]
    LocalFirst[Search Local RAG first]
    LocalIndex[Semantic Local Index]
    Enough{Enough evidence found?}
    Web[Web and news retrieval]
    Arxiv[arXiv retrieval]
    Score[Score, rank, and dedupe]
    Normalize[Normalize sources and findings]

    SubQuestion --> LocalFirst
    LocalFirst --> LocalIndex
    LocalIndex --> Enough
    Enough -- Yes --> Score
    Enough -- No --> Web
    Enough -- No --> Arxiv
    Web --> Score
    Arxiv --> Score
    Score --> Normalize
```

## Research Output Hydration Workflow

```mermaid
sequenceDiagram
    participant User as User
    participant Output as Research Output
    participant Store as Zustand Output Store
    participant Cache as Persisted Session Cache
    participant API as FastAPI
    participant SSE as SSE Stream

    User->>Output: Open output route
    Output->>Store: Restore UI state
    Output->>Cache: Load session snapshot by sessionId
    Cache-->>Output: Immediate cached render
    Output->>API: GET /api/research/{id}/state
    API-->>Output: Fresh session
    Output->>Store: Persist refreshed state
    Output->>SSE: Connect when session is running
    SSE-->>Output: Agent events and progress
    Output->>API: Refresh state after relevant events
```

## Detailed Progress Workflow

```mermaid
flowchart TD
    Start[Session running]
    Event[Agent emits status or result event]
    Persist[SessionStore persists event]
    Queue[SSE queue broadcasts event]
    TopBar[Top live progress bar updates]
    Panel[Detailed progress panel updates]
    Trace[Agent trace panel updates]

    Start --> Event
    Event --> Persist
    Event --> Queue
    Queue --> TopBar
    Queue --> Panel
    Queue --> Trace
```

## Comparative Analysis Workflow

```mermaid
flowchart TD
    Claims[Claims]
    Contradictions[Contradictions]
    Debate[Debate mode positions]
    Merge[Build comparative view model]
    Report[Comparative summary in report]
    UI[Comparative Analysis section]

    Claims --> Merge
    Contradictions --> Merge
    Debate --> Merge
    Merge --> Report
    Merge --> UI
```

## Dig Deeper Workflow

```mermaid
flowchart TD
    Select[User selects finding, claim, or insight]
    Request["POST /api/research/{id}/dig-deeper"]
    FollowUp[Create focused follow-up session]
    Run[Run follow-up pipeline]
    Merge[Merge results back into parent session]
    Persist[Persist merged session]
    Refresh[Refresh output workspace]

    Select --> Request
    Request --> FollowUp
    FollowUp --> Run
    Run --> Merge
    Merge --> Persist
    Persist --> Refresh
```

## Documentation Workflow

```mermaid
flowchart LR
    DocsPage[Docs route]
    Tabs[Project Reference, Architecture, Workflows]
    DocsAPI["/api/docs/..."]
    Files[Markdown files in repo]
    Mermaid[Mermaid rendering in UI]

    DocsPage --> Tabs
    Tabs --> DocsAPI
    DocsAPI --> Files
    Files --> Mermaid
    Mermaid --> DocsPage
```

## Recovery and Persistence Workflow

```mermaid
flowchart TD
    Run[Active research run]
    Persist[Persist session, events, and trace]
    Restart{Server restart occurs?}
    Recover[Load persisted session from SQLite]
    Mark[Mark interrupted run as failed recovery state]
    Restore[Output route can still restore the session]

    Run --> Persist
    Persist --> Restart
    Restart -- No --> Persist
    Restart -- Yes --> Recover
    Recover --> Mark
    Mark --> Restore
```

## Notes

- `Research Setup` is the entry and draft-preserving workspace.
- `Research Output` is the persistent analysis workspace.
- browser-cached provider setup is now part of the real workflow.
- docs are a first-class in-product evaluation surface.
- local RAG remains the first retrieval path when enabled.
- LLM reasoning is primary, but fallback behavior still exists when providers are unavailable.
