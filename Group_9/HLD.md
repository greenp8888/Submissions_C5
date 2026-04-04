High-Level Design: Multi-Agent AI Deep Researcher

Hackathon: Outskill AI Accelerator C5
Build window: 24 hours
Team size: 6
Primary UI: Gradio
Stretch UI: React

Goal
Build a multi-agent deep research system that can:
- research public information from web, news, and academic sources
- accept uploaded research material from the user
- create a local Agentic RAG knowledge base from those uploads
- blend local and public retrieval in one grounded report pipeline

Target users
- knowledge workers who need to ramp up quickly on unfamiliar topics
- analysts who need evidence-backed answers across multiple source types
- students and academics exploring a topic across papers, news, reports, and the web
- decision-makers who need a balanced view of competing claims before acting

Core value proposition
Ask a complex research question in plain language and receive a structured, citation-backed report that synthesizes findings from local documents, the web, academic papers, reports, and news. The system highlights contradictions, shows confidence and trust signals, surfaces inferred insights, and lets the user dig deeper on any finding, claim, or insight.


1. System Overview

Architecture

```text
User
  |
  v
Gradio UI (primary) / React UI (stretch)
  |
  v
FastAPI Service
  |- POST /api/research
  |- GET  /api/research/:id/stream
  |- GET  /api/research/:id/state
  |- GET  /api/research/:id/report
  |- GET  /api/research/:id/graph
  |- GET  /api/research/:id/trace
  |- POST /api/research/:id/dig-deeper
  |- GET  /api/research/:id/export/:fmt
  |- POST /api/knowledge/upload
  |- GET  /api/knowledge/collections
  |- GET  /api/knowledge/collections/:id
  |
  v
LangGraph Orchestration
  |- Orchestrator Agent / Coordinator
  |- Query Planning Agent
  |- Contextual Retriever Agent
  |   |- Web Retriever
  |   |- News Retriever
  |   |- Academic Retriever
  |   |- Academic Expansion Adapters (Semantic Scholar / PubMed)
  |   |- News Expansion Adapters (NewsAPI / GDELT)
  |   |- Reports / API Connector Adapters
  |   |- Local Retriever
  |   `- PDF Fallback Retriever
  |- Critical Analysis Agent
  |- Contradiction Detection Agent
  |- Source Validator Agent
  |- Insight Generation Agent
  |- Hypothesis Agent
  `- Report Builder Agent
  |
  v
Session Store + Event Bus
  |- in-memory ResearchSession state
  `- asyncio.Queue per session for SSE streaming

Local Agentic RAG sidecar
Upload files -> Parse -> Chunk -> Embed -> Local index -> Collection metadata
                                              |
                                              v
                                   Local Retriever / Query Router

External services
  |- OpenRouter (LLM)
  |- Tavily (primary web + news)
  |- arXiv API (primary academic)
  |- Semantic Scholar (academic expansion)
  |- PubMed (academic expansion)
  |- NewsAPI (news expansion)
  `- GDELT Project (news / events expansion)
```

Key design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Orchestration | LangGraph StateGraph | Natural fit for parallel fan-out, reducers, and conditional routing |
| LLM provider | OpenRouter | OpenAI-compatible API and one integration point for all agents |
| Public search | Tavily + arXiv as primary, provider adapters for Semantic Scholar / PubMed / NewsAPI / GDELT | Keeps MVP setup small while preserving expansion paths required by the product spec |
| Local RAG store | FAISS on disk + JSON/SQLite metadata | Local-first, hackathon-friendly, no managed vector DB required |
| Upload parsing | PDF first, extensible to TXT/MD/DOCX/CSV | Covers research uploads quickly while leaving room to expand |
| Session store | In-memory dict | Fastest option for demo scope |
| Streaming | SSE | Simpler than WebSockets and enough for live progress |
| Primary UI | Gradio | Python-native and fast to demo |

Agentic RAG extension

This design treats uploaded research material as a first-class source, not a one-off PDF attachment. The user can upload files into a local collection, the system indexes them locally, and the planner plus retrieval router decide whether each sub-question should use:
- public retrieval only
- local retrieval only
- hybrid retrieval across both

All local evidence is normalized into the same `Source` and `Finding` objects used by the rest of the pipeline. That means contradiction analysis, insight generation, citations, and reporting work the same way regardless of whether the evidence came from Tavily, arXiv, or an uploaded internal document.

Local RAG flow

1. User uploads research files into a session or named collection.
2. Ingestion service extracts text and metadata.
3. Chunking adds page-aware or section-aware spans.
4. Embedding service creates vectors.
5. Vectors and metadata are stored in a local index.
6. Planner sees a summary of available collections.
7. Query router chooses local, public, or hybrid retrieval per sub-question.
8. Local chunks are returned with chunk IDs and page references.
9. Downstream agents treat them as normal evidence.

Retrieval ordering and citation policy

1. When local uploads or indexed collections exist, local RAG is always searched first.
2. If indexing is incomplete, PDF fallback retrieval runs before any public retrieval.
3. Public retrieval runs in parallel only after local evidence is attached to the session.
4. Citation ordering prefers local evidence first, then web, then news, then academic and research sources.
5. Retrieval results are ranked by relevance and credibility, deduplicated, and truncated to top-k per source strategy.


2. Data Schema

All agent outputs append to a single `ResearchSession`. No agent overwrites another agent's work.

Core types

| Type | Fields | Set by |
|---|---|---|
| Source | `id, url, title, source_type(web/news/academic/report/api/pdf/local_upload), provider, author?, published_date?, credibility_score?, relevance_score?, rank?, duplicate_of_source_id?, snippet, collection_id?, page_refs?` | P3 Retrieval, updated by P4 |
| Finding | `id, sub_question, content, source_ids[], agent, raw` | P3 Retrieval |
| Claim | `id, statement, supporting_source_ids[], contradicting_source_ids[], confidence, confidence_pct, reasoning, contested` | P4 Critical Analysis |
| Contradiction | `id, claim_a, source_a_id, claim_b, source_b_id, analysis, resolution?` | P4 Critical Analysis |
| Insight | `id, content, evidence_chain[], insight_type(trend/cross_domain/hypothesis/gap), label` | P5 Insight Generator |
| Entity | `id, name, entity_type, description?, source_ids[]` | P5 Insight Generator |
| Relationship | `source_entity_id, target_entity_id, relationship_type, description?` | P5 Insight Generator |
| ReportSection | `section_type, title, content, order` | P6 Report Builder |
| FollowUpQuestion | `question, rationale` | P5 Insight Generator |
| ResearchEvent | `event_type, timestamp, agent?, message, data?` | Every agent |
| AgentTraceEntry | `id, agent, step, input_summary?, output_summary?, timestamp, token_estimate?` | P1 Orchestration |
| KnowledgeDocument | `id, collection_id, filename, document_type, checksum, upload_timestamp, status, page_count?, tags[]` | P3A Ingestion |
| DocumentChunk | `id, document_id, chunk_index, text, token_count, page_span?, embedding_id, keywords[]` | P3A Ingestion |
| LocalCollection | `id, name, description?, created_at, document_ids[], shared_scope(session/workspace)` | P3A Ingestion |

ResearchSession

| Field | Type | Description |
|---|---|---|
| `session_id` | string | Unique run ID |
| `query` | string | Original research question |
| `depth` | `quick \| standard \| deep` | Controls effort and routing |
| `status` | `pending \| running \| complete \| error` | Pipeline lifecycle |
| `sub_questions` | string[] | Planner output |
| `sources` | Source[] | Accumulated evidence sources |
| `findings` | Finding[] | Accumulated retrieved findings |
| `claims` | Claim[] | Consolidated claims |
| `contradictions` | Contradiction[] | Disagreements across evidence |
| `insights` | Insight[] | Higher-order synthesis |
| `entities` | Entity[] | Graph nodes |
| `relationships` | Relationship[] | Graph edges |
| `follow_up_questions` | FollowUpQuestion[] | Suggested next questions |
| `report_sections` | ReportSection[] | Final report payload |
| `events` | ResearchEvent[] | Append-only event log |
| `agent_trace` | AgentTraceEntry[] | Optional human-readable trace of orchestrator and agent activity |
| `uploaded_documents` | KnowledgeDocument[] | Documents attached to the session |
| `selected_collection_ids` | string[] | Local collections used for this run |
| `retrieved_chunks` | DocumentChunk[] | Top local chunks returned by local RAG |
| `pdf_texts` | string[] | Legacy raw extraction fallback before indexing |
| `debate_mode` | bool | Stretch comparative mode flag |
| `position_a` / `position_b` | string? | Stretch debate prompts |

Depth levels

| Feature | Quick (~2 min) | Standard (~5-8 min) | Deep (~15-20 min) |
|---|---|---|---|
| Sub-questions | 2-3 | 4-6 | 6-10 |
| Public sources | Web | Web + News + Academic | All public sources |
| Local corpus usage | If uploads exist | Hybrid retrieval when useful | Full collection-aware routing |
| Queries per sub-question | 1 | 2 | 3 |
| Contradiction analysis | Consolidation only | Full detection | Extended reasoning |
| Insights | Skip | 2-3 | Full |
| Entity extraction | Skip | Skip | Full |
| Knowledge graph | Skip | Skip | Full |
| Follow-up questions | 3 | 3-5 | 5 + gap analysis |


3. Component Specifications

Integration contract

Every agent is a pure function over `ResearchSession`:
- input: reads only the fields it needs
- output: returns a partial update merged through LangGraph reducers
- side effect: emits `ResearchEvent` entries to the session event queue

P1 - Orchestrator and Core

Owns
- `src/ai_app/schemas/research.py`
- `src/ai_app/schemas/report.py`
- `src/ai_app/domain/enums.py`
- `src/ai_app/llms/client.py`
- `src/ai_app/llms/structured_output.py`
- `src/ai_app/llms/retry.py`
- `src/ai_app/orchestration/graph.py`
- `src/ai_app/orchestration/state.py`
- `src/ai_app/orchestration/coordinator.py`
- `src/ai_app/memory/session_store.py`
- `src/ai_app/main.py`
- `src/ai_app/api/research.py`
- `src/ai_app/config.py`

Responsibilities
- define all shared schemas
- act as the main orchestrator receiving the user question and coordinating all downstream stages
- manage the LangGraph state machine
- handle session lifecycle and SSE streaming
- expose REST endpoints
- route between quick, standard, and deep flows
- maintain optional agent trace records for explainability

AI engineering concepts learned
- LangGraph reducers
- parallel fan-out
- conditional routing
- SSE streaming
- async coordination

P2 - Query Planner

Owns
- `src/ai_app/agents/planner_agent.py`
- `prompts/system/planner.txt`
- `prompts/task/deep_research.txt`

Responsibility
Break the user's question into independent sub-questions that can be investigated in parallel.

Input
- `query`
- `depth`
- `pdf_texts`
- `selected_collection_ids`
- summary of uploaded/local documents

Output
- `{ sub_questions: string[] }`

Behavior by depth
- Quick: 2-3 orthogonal sub-questions
- Standard: 4-6 sub-questions plus suggested source types
- Deep: 6-10 hierarchical sub-questions with second-order angles

Agentic RAG requirement
If local documents are available, the planner should mark which sub-questions are best answered from:
- local corpus
- public sources
- both

P3 - Retrieval Agents

Owns
- `src/ai_app/agents/contextual_retriever_agent.py`
- `src/ai_app/agents/web_retriever.py`
- `src/ai_app/agents/news_retriever.py`
- `src/ai_app/agents/academic_retriever.py`
- `src/ai_app/agents/academic_expansion_retriever.py`
- `src/ai_app/agents/news_expansion_retriever.py`
- `src/ai_app/agents/report_api_retriever.py`
- `src/ai_app/agents/local_retriever.py`
- `src/ai_app/agents/pdf_retriever.py`
- `src/ai_app/retrieval/chunking.py`
- `src/ai_app/retrieval/source_scoring.py`
- `src/ai_app/retrieval/citation_builder.py`
- `src/ai_app/retrieval/deduper.py`
- `src/ai_app/retrieval/provider_adapters.py`

Responsibility
For each sub-question, retrieve evidence from the right source and convert it into structured `Source` and `Finding` records.

Retrieval rules
- search local RAG first whenever local material exists
- refine public queries using locally retrieved evidence
- rank results by relevance and credibility
- deduplicate near-identical sources
- enforce top-k limits per provider and per sub-question
- keep provider names and provenance in normalized source records

Input
- `sub_questions[]`
- `depth`
- `selected_collection_ids[]`

Output
- `{ findings: Finding[], sources: Source[], retrieved_chunks?: DocumentChunk[] }`

Variants

| Variant | Source | Notes |
|---|---|---|
| Web | Tavily general search | Used at all depths |
| News | Tavily news filter | Standard and Deep only |
| Academic | arXiv API | Standard and Deep only |
| Academic expansion | Semantic Scholar / PubMed | Optional broader coverage for papers and medical literature |
| News expansion | NewsAPI / GDELT | Optional broader coverage and event monitoring |
| Reports / APIs | Structured report feeds or domain APIs | Optional connectors for richer stakeholder and market research |
| Local | FAISS over uploaded research | Used whenever a selected collection or session upload exists |
| PDF fallback | Raw uploaded PDF text | Only used if files are uploaded but not fully indexed yet |

AI engineering concepts learned
- agentic RAG
- query routing
- multi-source retrieval
- chunking and embeddings
- citation grounding

P3A - Local Knowledge Ingestion and Agentic RAG Router

Owns
- `src/ai_app/services/document_ingestion_service.py`
- `src/ai_app/retrieval/document_parser.py`
- `src/ai_app/retrieval/local_index.py`
- `src/ai_app/retrieval/query_router.py`
- `src/ai_app/api/knowledge.py`

Responsibility
Turn uploaded research material into a reusable local knowledge base and decide when to use it.

Input
- `files[]`
- `query`
- `selected_collection_ids[]`

Output
- `{ uploaded_documents, selected_collection_ids, retrieved_chunks, sources, findings }`

Expected behavior
- upload files into a collection
- extract text and metadata
- chunk with page or section spans
- create embeddings
- store vectors locally
- route queries to local, public, or hybrid retrieval
- keep citations grounded to exact chunk and page metadata

MVP scope
- PDF is mandatory
- TXT and Markdown are easy additions
- DOCX and CSV are optional if time remains

P4 - Critical Analysis

Owns
- `src/ai_app/agents/critical_analysis_agent.py`
- `src/ai_app/agents/contradiction_checker_agent.py`
- `src/ai_app/agents/source_verifier_agent.py`
- `src/ai_app/evaluators/contradiction_detection.py`
- `src/ai_app/evaluators/source_credibility_eval.py`
- `src/ai_app/evaluators/faithfulness.py`

Responsibility
Convert retrieved findings into claims, identify contradictions, and assess credibility.

Additional outputs
- highlight weak or uncertain evidence
- explain why one source is more credible than another
- assign confidence levels and support the UI trust meter

Input
- `findings[]`
- `sources[]`

Output
- `{ claims, contradictions, sources }`

P5 - Insight Generator and Knowledge Graph

Owns
- `src/ai_app/agents/insight_generation_agent.py`
- `src/ai_app/agents/hypothesis_agent.py`
- `src/ai_app/evaluators/citation_coverage.py`
- `src/ai_app/evaluators/report_completeness.py`

Responsibility
Generate cross-source insights, hypotheses, graph entities, graph edges, and follow-up questions.

Expected behavior
- detect emerging trends
- identify patterns across data
- produce evidence-backed hypotheses

Input
- `claims[]`
- `contradictions[]`
- `sources[]`

Output
- `{ insights, entities, relationships, follow_up_questions }`

P6 - Report Builder and Gradio UI

Owns
- `src/ai_app/agents/report_builder_agent.py`
- `src/ai_app/services/report_service.py`
- `src/ai_app/services/export_service.py`
- `ui/gradio/deep_researcher.py`
- `ui/components/query_input.py`
- `ui/components/run_timeline.py`
- `ui/components/report_viewer.py`
- `ui/components/evidence_table.py`
- `ui/components/source_list.py`
- `ui/components/citation_panel.py`
- `ui/components/confidence_badge.py`
- `ui/components/graph_panel.py`
- `ui/components/agent_trace_view.py`
- `ui/components/cost_panel.py`

Responsibility
Render the full session into a grounded markdown report and expose it in the Gradio UI.

Reporting requirements
- organize content into clear sections
- maintain inline citations for every material claim
- include contested claims, confidence signals, and weak-evidence callouts
- include evidence-backed insights and actionable recommendations when appropriate
- keep findings and AI-generated inference visually distinct

Sections by depth
- Quick: executive summary, key findings
- Standard: plus contested claims, insights, follow-ups, appendix
- Deep: full report plus graph data and expanded source appendix


4. User Story to Component Mapping

| User Story | Components | Output |
|---|---|---|
| US1 Ask a research question | Gradio input, FastAPI `/api/research`, Planner | Session created and sub-questions generated |
| US1A Upload local research corpus | Gradio upload panel, FastAPI `/api/knowledge/upload`, P3A ingestion | Collection indexed locally and available for retrieval |
| US2 Choose research depth | Gradio selector, `config.py`, all agents | Agent behavior changes by depth |
| US3 Watch research happen | SSE stream, progress log, `ResearchEvent` | Live activity feed |
| US4 Read a structured report | Report builder, markdown viewer | Summary, findings, appendix |
| US5 See where sources disagree | Critical analysis, contested claims section | Contradiction pairs with reasoning |
| US6 See confidence matrix | Claim scoring, data table, trust badge | Support/contradict counts, confidence, and trust signals |
| US7 Explore knowledge graph | Entity extraction, graph panel | Clickable node-edge graph with report linking |
| US8 Dig deeper on any point | `/dig-deeper`, focused planner flow | New findings appended to same session from a finding, claim, or insight |
| US9 See inferred insights | Insight generator, report section | Evidence-backed AI inference |
| US10 Get follow-up questions | Hypothesis agent, clickable list | New research entry points |
| US11 Export the report | Export endpoints and UI | Downloadable markdown and PDF |
| US12 Voice input (stretch) | Gradio audio + STT | Query from microphone |
| US13 Debate mode (stretch) | Dual input, comparative flow | Evidence table for both sides |
| US14 Agent trace view (stretch) | SSE event history, trace viewer | Human-readable view of orchestrator and agent steps |


5. API Contract

POST `/api/research`

Request
```json
{
  "query": "string",
  "depth": "quick | standard | deep",
  "files": ["optional session files"],
  "collection_ids": ["optional local collections"],
  "use_local_corpus": true
}
```

Response
```json
{
  "session_id": "string",
  "status": "running"
}
```

GET `/api/research/:id/stream`

SSE event payload
```json
{
  "event_type": "status | finding | claim | contradiction | insight | entity | relationship | report_section | follow_up | trace | complete | error",
  "timestamp": "ISO-8601",
  "agent": "optional",
  "message": "string",
  "data": {}
}
```

GET `/api/research/:id/state`
- response: full `ResearchSession`

GET `/api/research/:id/report`
- response: `{ "sections": ReportSection[] }`

GET `/api/research/:id/graph`
- response: `{ "nodes": Entity[], "edges": Relationship[] }`

GET `/api/research/:id/trace`
- response: `{ "trace": AgentTraceEntry[] }`

POST `/api/research/:id/dig-deeper`

Request
```json
{
  "finding_id": "string"
}
```

or

```json
{
  "claim_id": "string"
}
```

or

```json
{
  "insight_id": "string"
}
```

Response
```json
{
  "session_id": "same-session-id"
}
```

GET `/api/research/:id/export/:fmt`
- `fmt`: `markdown | pdf`

POST `/api/knowledge/upload`

Request
- multipart form-data
- `files[]`
- `collection_name`
- optional `tags[]`

Response
```json
{
  "collection_id": "string",
  "document_ids": ["string"],
  "status": "uploaded | indexing | indexed"
}
```

GET `/api/knowledge/collections`
- response: `{ "collections": LocalCollection[] }`

GET `/api/knowledge/collections/:id`
- response: `{ "collection": LocalCollection, "documents": KnowledgeDocument[] }`


6. Gradio UI Specification

Primary demo interface
- can call the pipeline directly for speed
- can also use FastAPI endpoints for clearer architecture

Layout

| Panel | Component | Story |
|---|---|---|
| Research question | `gr.Textbox` | US1 |
| Research library upload | `gr.File(file_types=[".pdf", ".txt", ".md", ".docx", ".csv"], file_count="multiple")` | US1, US1A |
| Collection selector | `gr.Dropdown(multiselect=True)` | US1A |
| Indexing status | `gr.Markdown` or `gr.DataFrame` | US1A |
| Depth selector | `gr.Radio(["Quick", "Standard", "Deep"])` | US2 |
| Start research | `gr.Button` | US1 |
| Live progress log | `gr.Textbox` or `gr.Chatbot` streaming | US3 |
| Report tab | `gr.Markdown` | US4, US5, US9 |
| Confidence matrix | `gr.DataFrame` | US6 |
| Trust badge / meter | `gr.Markdown` or `gr.HTML` | US6 |
| Knowledge graph | `gr.HTML` | US7 |
| Agent trace tab | `gr.DataFrame` or `gr.Markdown` | US14 |
| Dig deeper buttons | button list | US8 |
| Follow-up questions | button or radio list | US10 |
| Export actions | download buttons | US11 |
| Voice input | `gr.Audio` | US12 |
| Debate inputs | dual textbox layout | US13 |

Streaming pattern
The Gradio app should consume generator-style progress updates so users see retrieval, analysis, and report-building events as they happen.

Graph interaction pattern
- Deep mode graph should build progressively as entities and relationships are emitted
- clicking a node should highlight related report references and evidence rows when feasible in MVP scope


7. Work Division

| Person | Workstream | AI concepts | Key files |
|---|---|---|---|
| P1 | Orchestrator and Core | LangGraph, SSE, async state | `schemas/research.py`, `orchestration/graph.py`, `api/research.py`, `main.py` |
| P2 | Query Planner | structured output, prompt design | `agents/planner_agent.py`, planner prompts |
| P3 | Retrieval Agents + Local RAG | agentic RAG, embeddings, routing, ranking, dedupe | `agents/*retriever.py`, `retrieval/local_index.py`, `services/document_ingestion_service.py` |
| P4 | Critical Analysis | contradiction detection, LLM-as-judge | `critical_analysis_agent.py`, `contradiction_checker_agent.py`, evaluators |
| P5 | Insights + Graph | synthesis, entity extraction, hypotheses, graph UX | `insight_generation_agent.py`, `hypothesis_agent.py` |
| P6 | Report + Gradio UI | report generation, streaming UI, trust display, trace UX | `report_builder_agent.py`, `ui/gradio/deep_researcher.py`, UI components |

Integration rule
`schemas/research.py` is the shared contract and should be locked early.


8. Build Order

Phase 1 - Foundation (Hours 0-3)

Goal
Everyone can run their own piece independently against typed mock data.

Deliveries
- P1: FastAPI skeleton, session store, SSE scaffold, LangGraph stub
- P2: planner stub returning hardcoded sub-questions
- P3: web retriever working plus local ingestion skeleton
- P4: analysis stub over mock findings
- P5: insight stub over mock claims
- P6: Gradio shell with query box, upload panel, progress panel, mock report

Phase 2 - Vertical Slice MVP (Hours 3-8)

Goal
One end-to-end path works in Gradio.

Deliveries
- P1: wire planner -> retrieval -> analysis -> report
- P2: real decomposition prompts
- P3: web retriever + basic local upload parse/index flow
- P4: claim consolidation + basic confidence
- P5: initial insights
- P6: real streaming progress, report rendering, and starter confidence / trust display

Phase 3 - Full Feature Set (Hours 8-14)

Goal
All core stories work including local corpus retrieval.

Deliveries
- P1: all retrieval nodes in graph, knowledge upload endpoints, dig-deeper route
- P2: deeper planning and source hints
- P3: local RAG complete with chunking, embeddings, collection reuse, PDF fallback, ranking, top-k, and dedupe
- P4: contradiction detection + source verification + weak-evidence highlighting
- P5: entities, relationships, follow-up questions, and progressive graph updates
- P6: confidence tab, trust display, graph tab, collection selector, export actions, insight dig-deeper flow

Phase 4 - Quality and Export (Hours 14-19)

Goal
Stabilize, polish, and make the demo reliable.

Deliveries
- P1: export endpoints and error handling
- P2: prompt tuning
- P3: retrieval quality, provider adapter hardening, chunk-size tuning
- P4: calibration, contradiction quality, and trust meter quality
- P5: graph cleanup, entity dedupe, and node-to-report linking
- P6: polish UI, trace view, and export UX

Phase 5 - Stretch and Demo Prep (Hours 19-24)

Deliveries
- debate mode
- voice input
- optional Semantic Scholar / PubMed / NewsAPI / GDELT live adapters beyond the primary MVP providers
- agent trace view polish
- optional React frontend
- end-to-end demo rehearsal


9. Test Cases

Story acceptance criteria

| Story | Given | When | Then |
|---|---|---|---|
| US1 Ask question | User enters query and depth | Clicks Start Research | Progress begins within 3 seconds |
| US1 Upload PDF | User uploads a PDF before running | Research runs | Findings cite uploaded material |
| US1A Upload local corpus | User uploads multiple research files | Indexing completes | Collection becomes selectable for later runs |
| US1A Local-only knowledge | User asks about content only present in uploaded docs | Research runs | Local sources are cited in the report |
| US2 Quick depth | Quick selected | Research completes | Finishes fast with summary + findings |
| US2 Deep depth | Deep selected | Research completes | Includes insights, contradictions, graph data |
| US3 Live progress | Research is running | User watches log | Sees agents, sources, and findings incrementally |
| US4 Report structure | Standard or Deep completes | User opens report | Sees sections, citations, appendix |
| US5 Contradiction | Two sources disagree | User opens report | Contested claim section is present |
| US6 Confidence matrix | Claims are generated | User opens matrix tab | Support, contradiction, and confidence are visible |
| US6A Trust meter | Claims are generated | User opens the report or confidence view | Trust or confidence signals are visually understandable |
| US7 Knowledge graph | Deep mode completes | User opens graph tab | Related entities appear as nodes and edges and can be linked back to report context |
| US8 Dig deeper | User selects a finding, claim, or insight | Clicks investigate further | New findings append to same session |
| US9 Insights | Standard or Deep completes | User opens report | Insights are labeled as AI-generated inference |
| US10 Follow-ups | Research completes | User opens follow-up panel | Clickable next questions appear |
| US11 Export markdown | Research completes | User downloads markdown | File contains citations and report structure |
| US11 Export PDF | Research completes | User downloads PDF | Rendered report is readable |
| US14 Agent trace view | Research is running or complete | User opens trace tab | Orchestrator and agent steps are visible in order |

Component-level tests

P2 - Query Planner

| Test | Input | Expected output |
|---|---|---|
| Basic decomposition | Alzheimer's treatments, standard | 4-6 sub-questions covering evidence, mechanisms, controversy |
| Avoid overlap | Any query | Sub-questions are not duplicates |
| Depth scaling | Same query, quick vs deep | Deep returns more and better-structured sub-questions |
| Local source awareness | Query + selected collection | Planner marks local vs public vs hybrid needs |

P3 - Retrieval and Local RAG

| Test | Input | Expected output |
|---|---|---|
| Index uploaded files | 2 PDFs + 1 markdown note | Documents parsed, chunked, embedded, indexed |
| Route to local corpus | Query only answerable from uploaded docs | `local_retriever` is used and sources are `local_upload` |
| Hybrid routing | Query needs internal notes plus public context | Local and public retrieval both run and provenance is preserved |
| Chunk citation grounding | PDF chunk from pages 4-5 | Source metadata contains page refs for reporting |
| PDF fallback | Upload exists but indexing is incomplete | Raw extracted text is still searchable for MVP |
| Ranking and top-k | Many candidate sources returned | Highest relevance and credibility sources are kept within top-k |
| Duplicate filtering | Same article appears from multiple providers | Duplicates are merged or suppressed |

P4 - Critical Analysis

| Test | Input | Expected output |
|---|---|---|
| Detect contradiction | Two findings disagree strongly | One contradiction item is created |
| No false contradiction | All findings support same claim | No contradiction items are created |
| Confidence scaling | 3 support, 1 contradict | Medium confidence, not High |
| Credibility differentiation | Peer-reviewed paper vs anonymous blog | Higher credibility for the paper |
| Weak evidence flag | Only low-quality or sparse evidence exists | Claim is marked low confidence with weak-evidence explanation |

P5 - Insight Generator

| Test | Input | Expected output |
|---|---|---|
| Insight beyond sources | Claims about A and B | Insight compares or connects them |
| Evidence chain | Any generated insight | At least two supporting source IDs |
| Entity extraction | Claims mention Biogen, amyloid, FDA | Correct entity types returned |
| Trend detection | Time-separated evidence indicates momentum | Insight identifies an emerging trend with evidence chain |


10. Risk Mitigation

Cut list in priority order

| Priority | Cut | Impact | When to cut |
|---|---|---|---|
| 1 | React frontend | None, Gradio is the demo | Anytime |
| 2 | Voice input and debate mode | None, stretch only | Anytime |
| 3 | Advanced reranking/query expansion | Low | If behind at hour 8 |
| 4 | Persistent multi-session library UX | Medium, use session-only uploads instead | If behind at hour 10 |
| 5 | Knowledge graph | Medium, replace with entity list | If behind at hour 12 |
| 6 | Dig deeper | Medium, user can rerun manually | If behind at hour 12 |
| 7 | News retriever | Low, web + academic still work | If behind at hour 8 |
| 8 | PDF export | Low, markdown export is enough | If behind at hour 16 |
| 9 | Extended reasoning | Low, agents still work | If behind at hour 16 |

Technical risks

| Risk | Mitigation |
|---|---|
| LLM latency makes Deep slow | Use per-agent timeouts and demo Standard mode |
| Tavily or arXiv is unavailable | Degrade gracefully and continue with remaining sources |
| Secondary providers are unavailable | Fall back to primary providers or continue with available evidence |
| Upload parsing fails | Log event, skip bad file, keep session alive |
| Large uploads make indexing slow | Cap size/page count, stream indexing status, allow session-only fallback |
| Local index corruption | Keep collection manifest and support rebuild from source files |
| Schema churn blocks integration | Lock shared schema early |
| P3 workload is too broad | Keep one local retriever plus one ingestion service and skip fancy ranking |


11. File Structure

Proposed structure aligned to the scaffold

```text
src/ai_app/
├── schemas/
│   ├── research.py
│   ├── report.py
│   ├── agent_io.py
│   └── run_state.py
├── domain/
│   └── enums.py
├── llms/
│   ├── client.py
│   ├── structured_output.py
│   ├── retry.py
│   └── embeddings.py
├── orchestration/
│   ├── graph.py
│   ├── state.py
│   └── coordinator.py
├── memory/
│   └── session_store.py
├── api/
│   ├── research.py
│   ├── knowledge.py
│   ├── reports.py
│   └── health.py
├── agents/
│   ├── base.py
│   ├── planner_agent.py
│   ├── contextual_retriever_agent.py
│   ├── web_retriever.py
│   ├── news_retriever.py
│   ├── academic_retriever.py
│   ├── local_retriever.py
│   ├── pdf_retriever.py
│   ├── critical_analysis_agent.py
│   ├── contradiction_checker_agent.py
│   ├── source_verifier_agent.py
│   ├── insight_generation_agent.py
│   ├── hypothesis_agent.py
│   ├── report_builder_agent.py
│   └── qa_review_agent.py
├── retrieval/
│   ├── chunking.py
│   ├── document_parser.py
│   ├── local_index.py
│   ├── query_router.py
│   ├── source_scoring.py
│   └── citation_builder.py
├── services/
│   ├── research_service.py
│   ├── document_ingestion_service.py
│   ├── report_service.py
│   └── export_service.py
├── evaluators/
│   ├── faithfulness.py
│   ├── contradiction_detection.py
│   ├── citation_coverage.py
│   └── report_completeness.py
├── observability/
│   ├── cost_tracking.py
│   ├── traces.py
│   └── agent_logs.py
├── workflows/
│   ├── deep_research_flow.py
│   └── comparative_analysis_flow.py
└── prompts/
    └── loader.py

prompts/
├── system/
│   ├── planner.txt
│   ├── retriever.txt
│   ├── analyst.txt
│   ├── contradiction_checker.txt
│   ├── verifier.txt
│   ├── insight.txt
│   └── reporter.txt
└── task/
    ├── deep_research.txt
    ├── build_report.txt
    └── compare_sources.txt

ui/
├── gradio/
│   └── deep_researcher.py
├── components/
│   ├── query_input.py
│   ├── run_timeline.py
│   ├── report_viewer.py
│   ├── evidence_table.py
│   ├── citation_panel.py
│   ├── source_list.py
│   ├── confidence_badge.py
│   ├── cost_panel.py
│   └── graph_panel.py
└── services/
    ├── api_client.py
    └── sse_client.py
```

Additional planned files for expanded requirement coverage
- `src/ai_app/agents/academic_expansion_retriever.py`
- `src/ai_app/agents/news_expansion_retriever.py`
- `src/ai_app/agents/report_api_retriever.py`
- `src/ai_app/retrieval/deduper.py`
- `src/ai_app/retrieval/provider_adapters.py`
- `ui/components/agent_trace_view.py`


12. Scaffold Alignment Notes

What stays out of scope

| Scaffold module | Why | Decision |
|---|---|---|
| `persistence/` | Full database is overkill for hackathon demo | Skip |
| `memory/long_term.py`, `memory_policies.py` | Generic agent memory is not needed | Skip |
| `api/ws.py` | SSE is enough | Skip |
| `ui/streamlit_hub/` | Gradio is the chosen UI | Skip |
| `orchestration/human_approval.py` | Human approval is a production concern | Skip |
| `retrieval/hybrid_search.py`, `retrieval/reranker.py`, `retrieval/query_expansion.py` | Advanced retrieval can wait | Optional only |
| `guardrails/` extras | Nice to have, not core to demo | Skip except basic input validation |
| heavy observability extras | Cost and traces are enough for demo | Skip |

Important change for local RAG

The previous design treated PDF retrieval as an in-memory shortcut. This HLD upgrades that into a local-first Agentic RAG subsystem:
- build a focused local index for uploaded research
- do not build a full generic long-term memory platform
- keep the local corpus grounded, small, and demo-oriented

Canonical agent mapping

| Canonical file | Role |
|---|---|
| `planner_agent.py` | Query decomposition |
| `web_retriever.py` | Tavily web search |
| `news_retriever.py` | Tavily news search |
| `academic_retriever.py` | arXiv retrieval |
| `academic_expansion_retriever.py` | Semantic Scholar and PubMed expansion |
| `news_expansion_retriever.py` | NewsAPI and GDELT expansion |
| `report_api_retriever.py` | Report and API connectors |
| `local_retriever.py` | Local collection retrieval |
| `pdf_retriever.py` | Upload fallback retrieval |
| `critical_analysis_agent.py` | Claim consolidation and confidence |
| `contradiction_checker_agent.py` | Cross-source contradiction detection |
| `source_verifier_agent.py` | Source validation and credibility scoring |
| `insight_generation_agent.py` | Trends and cross-domain connections |
| `hypothesis_agent.py` | Gaps and follow-up hypotheses |
| `report_builder_agent.py` | Structured markdown report |
| `qa_review_agent.py` | Optional faithfulness gate |

Scaffold gaps to fill

| Story | Gap | Where to build it |
|---|---|---|
| US1A Upload local research corpus | No dedicated upload/list API | `api/knowledge.py`, `document_ingestion_service.py`, Gradio collection panel |
| US7 Knowledge graph | No graph component | `ui/components/graph_panel.py` |
| US8 Dig deeper | No explicit route | `api/research.py` + graph sub-pipeline |
| US3 Live progress | Scaffold uses WebSocket patterns | Replace with SSE client/service |
| US12 Voice input | No audio component | Add `gr.Audio` if time remains |
| US14 Agent trace view | No dedicated trace UI | `ui/components/agent_trace_view.py` + `/api/research/:id/trace` |
