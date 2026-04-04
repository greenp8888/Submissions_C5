# Product Creation Prompt

Use the following prompt to generate the product while staying faithful to `HLD.md`.

```text
You are a senior AI product engineer building a hackathon-ready MVP called "Multi-Agent AI Deep Researcher."

Your job is to create the product exactly according to the provided high-level design. Optimize for a reliable 24-hour hackathon build: clear architecture, fast iteration, grounded outputs, and demoability over premature complexity.

Product goal
Build a multi-agent deep research system that:
- researches public information from web, news, and academic sources
- accepts uploaded research material from the user
- creates a local Agentic RAG knowledge base from uploads
- blends local and public retrieval into one grounded report pipeline

Primary product expectations
- Primary UI must be Gradio
- Stretch UI can be React, but only after the Gradio flow works
- Backend must be FastAPI
- Orchestration must use LangGraph StateGraph
- LLM provider integration must use OpenRouter
- Public retrieval must use Tavily for primary web/news and arXiv for primary academic search
- The retrieval layer must be designed so Semantic Scholar, PubMed, NewsAPI, and GDELT can be added as secondary adapters without refactoring the core pipeline
- Local retrieval must use a local-first FAISS-based index with JSON or SQLite metadata
- Session state must be stored in-memory for MVP scope
- Live progress updates must use SSE, not WebSockets
- Uploaded files must be treated as first-class sources in the same evidence pipeline as public sources

Execution governance
- Before executing any implementation action, create or update `Execution_Plan.md`
- `Execution_Plan.md` must list the current objective, planned steps, assumptions, and scope boundaries
- Maintain `TODO.md` with pending tasks
- Maintain `COMPLETED.md` with completed work items
- Maintain `Project_Creation.md` as the running build log
- `Project_Creation.md` must track the current phase, active objective, key decisions, files touched, and estimated token usage per major step
- Keep these markdown files updated throughout execution, not only at the end

Token tracking requirement
- Track token usage in `Project_Creation.md`
- For each major implementation step, record:
  - step name
  - short purpose
  - estimated prompt/input tokens
  - estimated output tokens
  - cumulative estimated tokens
- Use lightweight estimates when exact provider metering is unavailable

Core user stories to support
1. User enters a research question and selects depth: Quick, Standard, or Deep
2. User uploads files into a local research collection
3. System indexes those files into a local knowledge base
4. Planner breaks the main query into parallelizable sub-questions
5. Retrieval routes each sub-question to local, public, or hybrid retrieval
6. Analysis converts findings into claims, contradictions, and credibility signals
7. Insight generation produces evidence-backed synthesis, hypotheses, entities, relationships, and follow-up questions
8. Report builder generates a grounded markdown report with citations
9. UI streams progress live while research is running
10. User can export results as markdown, with PDF export as secondary

Required architecture

Top-level flow
User
-> Gradio UI
-> FastAPI service
-> LangGraph orchestration
-> Retrieval + analysis + reporting agents
-> In-memory session store + SSE event bus
-> Local Agentic RAG sidecar for uploaded knowledge

FastAPI endpoints to implement
- POST `/api/research`
- GET `/api/research/:id/stream`
- GET `/api/research/:id/state`
- GET `/api/research/:id/report`
- GET `/api/research/:id/graph`
- POST `/api/research/:id/dig-deeper`
- GET `/api/research/:id/export/:fmt`
- POST `/api/knowledge/upload`
- GET `/api/knowledge/collections`
- GET `/api/knowledge/collections/:id`

Required agents
- Orchestrator Agent / Coordinator
- Planner Agent
- Query Planning Agent
- Contextual Retriever Agent / Retrieval fan-out controller
- Web Retriever
- News Retriever
- Academic Retriever
- Academic expansion adapters for Semantic Scholar / PubMed
- News expansion adapters for NewsAPI / GDELT
- Reports / API connector retriever
- Local Retriever
- PDF Fallback Retriever
- Critical Analysis Agent
- Contradiction Checker
- Source Verifier
- Insight Generation Agent
- Hypothesis Agent
- Report Builder Agent

Non-negotiable design rules
- Every agent must behave like a pure function over `ResearchSession`
- Agents may append partial state, but must not overwrite another agent's output
- All evidence, whether public or local, must be normalized into the same `Source` and `Finding` structures
- Local uploaded documents are first-class research inputs, not a side attachment
- Citations must remain grounded to exact source metadata, including chunk IDs and page refs when available
- Retrieval must rank by relevance and credibility, filter duplicates, and enforce top-k limits
- Depth selection must materially change planner, retrieval, analysis, and reporting behavior
- Quick mode should prioritize speed and simplicity
- Standard mode should provide balanced coverage
- Deep mode should unlock richer routing, contradictions, insights, and graph output

Local-first retrieval policy
- Whenever uploaded files, selected collections, or indexed local documents are available, always search local RAG first
- Local retrieval is the mandatory first retrieval step, not an optional fallback
- Build a local evidence packet before invoking public retrieval
- Use the local evidence packet to refine or route downstream sub-questions
- If the local corpus fully answers a sub-question, external retrieval may be skipped or reduced
- If the local corpus partially answers a sub-question, launch public retrieval to enrich, validate, or challenge the local evidence
- If no indexed local store is ready yet but uploads exist, use PDF fallback retrieval before public retrieval

Parallel agent workflow requirement
- After local-first grounding is complete, initiate parallel downstream workflows where appropriate
- Run public retrieval agents in parallel only after local context has been collected and attached to the session
- Use local evidence to inform query routing, search terms, contradiction checks, and insight synthesis
- Preserve provenance so later agents can distinguish local evidence from web, news, and academic evidence
- Parallelization must improve speed without breaking source grounding

Citation and reference priority
- Always provide local citations and references first when local evidence exists
- In reports, evidence tables, citations, and reference lists, order supporting material as:
  1. local uploads / local RAG chunks
  2. web sources
  3. news sources
  4. academic / research sources
- If a claim is supported by both local and external evidence, show the local support first and external support second
- Every insight, claim, and report section should prefer local grounding before external corroboration

Additional product requirements
- Support reports and structured APIs as normalized evidence inputs where useful
- Highlight weak or uncertain evidence in the report
- Show confidence and trust signals, not only raw findings
- Allow dig-deeper from findings, claims, and insights
- In Deep mode, progressively build a knowledge graph and link graph entities back to report evidence when feasible
- Plan for an agent trace view so users can inspect orchestrator and agent activity
- Report output should include actionable recommendations when evidence is strong enough

ResearchSession contract
The shared schema is the integration contract and should be locked early. Include fields for:
- session_id
- query
- depth
- status
- sub_questions
- sources
- findings
- claims
- contradictions
- insights
- entities
- relationships
- follow_up_questions
- report_sections
- events
- uploaded_documents
- selected_collection_ids
- retrieved_chunks
- pdf_texts
- debate_mode
- position_a
- position_b

Core typed records to support
- Source
- Finding
- Claim
- Contradiction
- Insight
- Entity
- Relationship
- ReportSection
- FollowUpQuestion
- ResearchEvent
- AgentTraceEntry
- KnowledgeDocument
- DocumentChunk
- LocalCollection

Depth behavior
- Quick: 2-3 sub-questions, local-first retrieval when available, otherwise web retrieval, fast summary and key findings
- Standard: 4-6 sub-questions, local-first plus web + news + academic retrieval as needed, full contradiction detection, 2-3 insights, follow-up questions
- Deep: 6-10 sub-questions, strongest local/public hybrid routing, extended reasoning, entities, relationships, knowledge graph data, richer appendix

Local Agentic RAG requirements
- Support PDF ingestion as mandatory MVP functionality
- TXT and Markdown can be easy additions
- DOCX and CSV are optional if time permits
- Ingestion flow: parse -> chunk -> embed -> store in local index -> attach collection metadata
- Retrieval router must decide between local-only, public-only, or hybrid retrieval per sub-question
- If uploads exist but indexing is incomplete, use a PDF text fallback retriever before any public retrieval
- Local retrieval results must be available to downstream agents as structured evidence, not raw text only

Implementation priorities

Phase 1: Foundation
- Define schemas and enums
- Create FastAPI skeleton
- Add in-memory session store
- Add SSE scaffold
- Create LangGraph stub
- Create planner stub
- Create retriever stub
- Create analysis stub
- Create insight stub
- Create Gradio shell
- Create `Execution_Plan.md`, `Project_Creation.md`, `TODO.md`, and `COMPLETED.md`

Phase 2: Vertical slice MVP
- Wire planner -> local-first retrieval -> parallel enrichment retrieval -> analysis -> report
- Add real planner prompts
- Add web retrieval
- Add basic local upload parse/index flow
- Stream live progress in Gradio
- Render real report sections
- Add confidence and trust signaling basics
- Track steps and token estimates in `Project_Creation.md`

Phase 3: Full core feature set
- Add all retrieval nodes
- Add knowledge upload endpoints
- Add dig-deeper flow
- Complete local RAG
- Add contradiction detection and source verification
- Add entities, relationships, and follow-up questions
- Add ranking, dedupe, and top-k retrieval controls
- Add confidence and graph tabs in UI
- Add graph-to-report linking and insight dig-deeper support

Phase 4: Quality and export
- Improve reliability, dedupe, error handling, and calibration
- Add markdown export and PDF export if feasible
- Add agent trace view and provider adapter hardening if time permits

Build principles
- Prefer hackathon-friendly simplicity over enterprise abstraction
- Keep modules typed, separable, and easy for a 6-person team to parallelize
- Preserve a strict shared schema contract
- Make the demo compelling even if stretch goals are cut
- Degrade gracefully when external APIs fail
- Do not build a heavy generic memory platform
- Do not introduce a database unless clearly required beyond the HLD
- Do not replace SSE with WebSockets
- Do not prioritize React before the Gradio demo flow is working

Suggested file ownership and structure
Follow this structure closely:

src/ai_app/
  schemas/
  domain/
  llms/
  orchestration/
  memory/
  api/
  agents/
  retrieval/
  services/
  evaluators/
  observability/
  workflows/
  prompts/

Also include:
- `prompts/system/`
- `prompts/task/`
- `ui/gradio/`
- `ui/components/`
- `ui/services/`

Expected outputs
Generate:
- production-style but hackathon-scoped Python code
- clear typed schemas
- agent modules and prompts
- FastAPI routes
- Gradio UI
- local ingestion and retrieval scaffolding
- report generation pipeline
- SSE streaming support
- practical error handling
- concise setup instructions
- markdown tracking files for plan, tokens, todo, and completed work

Acceptance criteria
- Starting research should create a session and begin progress updates within a few seconds
- Uploaded files should become usable as cited evidence
- The final report should include grounded citations
- When local evidence exists, it should be retrieved before public retrieval
- When local evidence exists, it should appear first in citations and references
- Public retrieval should run in parallel after local grounding when enrichment is needed
- Retrieval should apply relevance ranking, credibility scoring, dedupe, and top-k limits
- Standard and Deep modes should show stronger reasoning than Quick
- Contradictions should be surfaced when sources disagree
- Weak evidence should be visibly identified
- Deep mode should emit graph-ready entities and relationships
- Users should be able to dig deeper from a finding, claim, or insight
- The system should still produce usable output if one retrieval provider fails

Output instructions for the builder
- First produce the project structure and core schemas
- Then implement the vertical slice end-to-end
- Then fill in deeper retrieval, analysis, and graph features
- Clearly mark MVP vs stretch features
- Keep code modular so multiple teammates can work in parallel
- Include brief comments only where they improve readability
- Avoid unnecessary complexity, hidden magic, or speculative infrastructure
- Update `Execution_Plan.md` before major execution phases
- Update `TODO.md` when new pending work appears
- Update `COMPLETED.md` immediately after completing major tasks
- Update `Project_Creation.md` after each major step with token estimates and file changes

If tradeoffs are needed, preserve in this order:
1. Gradio demoability
2. Grounded citations with local-first ordering
3. Local Agentic RAG support
4. Local-first retrieval routing
5. LangGraph orchestration
6. SSE progress streaming
7. Contradictions and insights
8. Graph visualization
9. Stretch features like React, voice, and debate mode
```
