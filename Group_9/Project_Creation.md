# Project Creation

## Current Phase
MVP implementation completed for initial runnable pass

## Active Objective
Build `Group_9/ai-hackathon` with:
- backend and UI inside a single app root
- local-first RAG and public enrichment flow
- FastAPI, Gradio, and LangGraph integration
- submission tracking updates during implementation

## Key Decisions
- Use `Execution_Plan.md` for pre-action planning
- Use `TODO.md` for pending work
- Use `COMPLETED.md` for finished work
- Use this file to track step-wise token estimates and major project decisions
- Expand the HLD without breaking the MVP-first architecture
- Treat Semantic Scholar, PubMed, NewsAPI, and GDELT as planned adapters or secondary providers rather than mandatory day-one integrations
- Keep agent trace view and richer graph UX in planned execution scope even if they land after the MVP slice
- Use graceful provider fallback because no API credentials are currently present in the environment
- Target Python 3.10 compatibility instead of 3.11-only syntax

## Files Touched
- `Group_9/Execution_Plan.md`
- `Group_9/HLD.md`
- `Group_9/Product_Creation_Prompt.md`
- `Group_9/Project_Creation.md`
- `Group_9/TODO.md`
- `Group_9/COMPLETED.md`
- `Group_9/ai-hackathon/*`

## Token Tracking

| Step | Purpose | Estimated Input Tokens | Estimated Output Tokens | Cumulative Estimated Tokens |
|---|---|---:|---:|---:|
| Review HLD and prompt | Capture current architecture and prompt gaps | 4500 | 300 | 4800 |
| Create execution plan | Establish pre-action workflow compliance | 350 | 180 | 5330 |
| Update product prompt | Add local-first, citation ordering, and tracking rules | 2400 | 1400 | 9130 |
| Create tracking files | Set up project management markdown files | 700 | 500 | 10330 |
| Gap analysis against requirements | Identify covered, partial, and missing requirements | 2600 | 900 | 13830 |
| Expand HLD and project plan | Add missing features, execution phases, and ownership | 3200 | 1800 | 18830 |
| Sync product prompt and trackers | Keep execution docs aligned with the revised HLD | 1200 | 700 | 20730 |
| Environment discovery | Confirm runtime, git status, and credential availability | 650 | 180 | 21560 |
| Create app root and core schemas | Build project config, shared models, and session store | 2800 | 1800 | 26160 |
| Implement agents, retrieval, and orchestration | Add local-first research pipeline and provider adapters | 5200 | 2400 | 33760 |
| Implement APIs and Gradio UI | Add backend routes, streaming, dig-deeper, export, and UI tabs | 4300 | 2200 | 40260 |
| Validation and dependency setup | Compile code, install dependencies, smoke test app import and local-first behavior | 2100 | 950 | 43310 |
| Add operations docs and scripts | Create extensive README plus start/stop scripts and verify lifecycle | 1500 | 700 | 45510 |

## Notes
- Token counts are estimated for project management only.
- Exact provider-level token metering is not available in this markdown workflow.
- Validation completed:
  - `python -m compileall Group_9\\ai-hackathon\\src Group_9\\ai-hackathon\\ui`
  - `pip install -e Group_9\\ai-hackathon`
  - `python -c "import ai_app.main"`
  - coordinator smoke test without provider keys
  - local-first ingestion and retrieval smoke test
  - `powershell -ExecutionPolicy Bypass -File .\\start.ps1 -Port 8011`
  - `GET http://127.0.0.1:8011/health`
  - `powershell -ExecutionPolicy Bypass -File .\\stop.ps1`
