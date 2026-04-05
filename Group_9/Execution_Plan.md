# Execution Plan

## Objective
Implement the `Group_9/ai-hackathon` MVP described by the revised HLD and product prompt, including:
- FastAPI backend and Gradio UI inside `Group_9/ai-hackathon`
- local-first research orchestration with LangGraph
- local ingestion and retrieval plus public-provider adapters
- SSE progress streaming, reports, graph, trace, and dig-deeper flows
- markdown execution tracking throughout implementation

## Planned Steps
1. Create the project root and top-level app files.
2. Implement shared schemas, config, session store, and LLM/provider clients.
3. Implement ingestion, retrieval, scoring, dedupe, and orchestration flow.
4. Implement FastAPI endpoints, export service, and SSE streaming.
5. Implement Gradio UI and component modules.
6. Add prompts, README, and environment examples.
7. Run validation checks and update markdown trackers with outcomes.

## Current Status
- Research-grade upgrade implemented on top of the runnable MVP
- Validation completed with compile, import, local-only, PDF page-reference, provider-settings-route, and batch/date-contract smoke checks
- Remaining work is deeper automated testing, richer graph UX, and stronger provider-backed analysis rather than core feature delivery

## Active Fix Scope
- fix arXiv retrieval redirect/runtime behavior
- add provider-key configuration from the UI for OpenRouter and Tavily
- make dig-deeper refresh the UI with updated session data
- improve visibility into available dig-deeper targets and provider status

## Current Full-Implementation Scope
- add user-controlled source toggles for Local RAG, Web/Tavily, and arXiv
- add date-range inputs with quick presets and propagate them through retrieval/reporting
- support user-entered multi-topic batch research without starter packs
- upgrade credibility scoring and expose methodology in outputs
- improve local PDF/RAG citations with file names, page numbers, and snippets
- replace markdown-dump PDF export with a more humanized document
- redesign the UI into a more production-like research workflow

## Implementation Outcome
- Added request/session contracts for source toggles, date presets, date range, and batch mode
- Added provider settings API routes and UI persistence flow for OpenRouter and Tavily
- Enforced local-first retrieval with source-aware routing and external date-window filtering
- Preserved filename and actual PDF page metadata through ingestion, retrieval, citations, and reports
- Expanded report sections to include methodology, source strategy, credibility evaluation, limitations, RAG references, and comprehensive bibliography
- Upgraded PDF export to a formatted narrative document instead of a raw markdown dump
- Simplified the Gradio UI into a production-style research console with setup, live progress, report, references, confidence, graph, trace, dig-deeper, and export areas
- Replaced the Gradio root UI with a React + Vite dashboard served by FastAPI static assets
- Added a frontend app shell, route-driven session pages, knowledge page, settings page, and React Flow graph view

## Notes
- Assumption: API credentials may be added later, so provider integrations must degrade gracefully when keys are missing.
- Assumption: Python 3.10 is the available runtime in this environment.
- Assumption: token tracking remains estimated at the markdown level unless exact API metering is implemented later.
