# Phase 2 Roadmap: Multi-Pass Deep Research

This document describes **Phase 2** of evolving the Local Multi-Agent Deep Researcher from a **single-pass** LangGraph pipeline into a **multi-pass** workflow: detect gaps, refine queries, retrieve again, merge evidence, and re-synthesize—without requiring the user to manually re-run the full job.

**Scope:** Phase 2 is delivered as **two parallel tracks** that ship together in **vertical slices**—**orchestration** (LangGraph, state, retrieval loop) and **UI** (`app.py` / Gradio)—so controls and surfaces are added **when** the backend capability lands. That avoids building multi-pass logic first and then reworking the layout twice.

**Still out of scope:** Full conversational chat, section-level “expand this” loops, URL-fetch verification, and persistence (see [Out of scope](#out-of-scope)).

**Related docs:** [ARCHITECTURE.md](./ARCHITECTURE.md) (current single-pass design), [FUNCTIONAL.md](./FUNCTIONAL.md) if present.

---

## 1. Objectives

1. **Closed-loop retrieval:** After an initial retrieve → analyze pass, the system identifies **what is still missing** or **under-supported** and issues **targeted follow-up retrieval**.
2. **Bounded cost and latency:** Multi-pass behavior must be **capped** (max rounds, max new queries, max evidence growth) and **configurable**.
3. **Traceability:** Each pass is visible in `trace` / `retrieval_log` so demos and debugging stay understandable.
4. **Backward compatibility:** A **“single pass”** mode (max rounds = 1) preserves today’s behavior for quick runs and tests.
5. **Research-oriented UI in the same phase:** Layout, controls, and visibility improvements ship **alongside** graph changes—not in a separate late UI pass—so there is no repeated integration or duplicate layout work.

---

## 2. Prerequisites (recommended before or in parallel)

These are not strictly blocking but reduce rework:

| Item | Rationale |
|------|-----------|
| Persist planner `objective` in `ResearchState` | Gap analysis can align follow-up queries with stated objective. |
| Optional **evidence IDs** (`e_1`, `e_2`, …) in `EvidenceItem` | Easier deduplication, merge semantics, and future citation links. |
| Configurable caps for analyst/report context | Phase 2 increases evidence volume; downstream nodes need sane limits. |

---

## 3. High-Level Flow (target)

```text
START → planner → prep_retrieval
           → [parallel retrievers] → retriever_merge
           → critical_analyst
           → gap_planner          ← new
           → should_continue?     ← new (conditional)
                 │ yes → prep_followup_retrieval → [subset of retrievers] → merge_new_evidence
                 │       → (increment round) → critical_analyst  (loop)
                 │ no  → insight_generator → report_builder → END
```

**Design choice:** Reuse existing retriever nodes where possible by passing **follow-up query lists** and **tool allowlists** in state, or add thin wrapper nodes that set those fields and delegate. Prefer **minimal duplication** in `graph.py`.

---

### 3.1 Parallel UI track (same phase, vertical slices)

Work **in the same PRs or adjacent commits** as the backend slice that needs the surface—do not defer UI to the end of Phase 2.

| Backend slice | UI work to ship with it |
|---------------|-------------------------|
| `max_research_rounds` in state / `Settings` | Gradio **slider or dropdown** (e.g. 1–3); label explains latency/cost; default **1**. |
| `gap_planner` + `gap_findings` in state | **Markdown panel** or accordion section **“Gaps / follow-up focus”** showing last round’s gaps and (optionally) the follow-up queries used—helps users trust multi-pass behavior. |
| Multi-pass `trace` / `retrieval_log` | Promote **orchestration + retrieval** into a **visible tab or column** (not only a collapsed accordion); show **round** in trace lines when `research_round > 1`. |
| Larger `evidence` lists | **Two-column or tabbed layout**: **Report** vs **Sources** (table + optional excerpt preview); avoid hiding all snippets behind a single toggle—e.g. show short excerpts inline or default **Detailed extracts** to expanded for the demo path. |
| `research_objective` from planner (if added) | Short **read-only box** under the question: “Planner objective” so the plan is visible before run completes. |

**Principles:** One **run** still returns one primary report; avoid rebuilding the whole UI twice. Prefer **Tabs** (`gr.Tabs`) or **Rows** with clear hierarchy so adding panels for gaps/rounds does not require another redesign later.

**Workflow:** When picking up a milestone (see §11), define both **graph tasks** and **`app.py` tasks** for that milestone before merging.

---

## 4. State Extensions (`deep_researcher/models.py`)

Add fields (names are suggestions; keep consistent once chosen):

| Field | Type | Purpose |
|-------|------|---------|
| `research_round` | `int` | Current pass index (starts at 1). |
| `max_research_rounds` | `int` | Stop condition (default 1 = current behavior; e.g. 2–3 for multi-pass). |
| `gap_findings` | `list[str]` | Human-readable gaps from LLM or structured output. |
| `followup_queries` | `list[str]` | Queries for the next retrieval round only. |
| `followup_tools` | `list[str]` or flags | e.g. `local`, `wikipedia`, `arxiv`, `tavily` — which channels to run in follow-up. |
| `evidence_by_round` | optional `list[list[EvidenceItem]]` | Audit trail per round (optional; can derive from logs instead). |

**Merge policy:** `merge_new_evidence` appends to `evidence` with **deduplication** (same URL, or same `(source_label, title, excerpt_prefix)` if no URL). Document the rule in code comments.

---

## 5. New and Modified Nodes (`deep_researcher/graph.py`)

### 5.1 `gap_planner` (new)

**Input:** `question`, `subquestions`, `analysis_summary`, `contradictions`, sample of `evidence` (or counts by `source_label`).

**Output (strict JSON preferred):**

- `gaps`: list of strings (what is missing, weak, or contradictory).
- `followup_queries`: 2–8 focused queries (empty if nothing useful to do).
- `tools`: which retrievers to invoke (subset of all four).

**Prompting guidelines:**

- Prefer **specific** queries over restating the original question.
- If evidence is already sufficient, return **empty** `followup_queries` to trigger exit.
- Respect **user toggles** (e.g. if web search disabled, do not suggest Tavily-only follow-up without local/arXiv fallback).

### 5.2 `should_continue` (conditional)

**Logic:**

- If `research_round >= max_research_rounds` → **no**.
- If `followup_queries` is empty → **no**.
- Else → **yes**.

### 5.3 Follow-up retrieval path

- Option A: **Reuse** parallel nodes with `queries = followup_queries` and skip channels not in `followup_tools`.
- Option B: Single `followup_retriever` node that calls `retrieval.py` helpers internally (less graph fan-out, easier gating).

**Recommendation:** Option A for consistency with timing logs and existing behavior; add small **gate** lambdas or pass state flags so disabled tools short-circuit.

### 5.4 `merge_new_evidence` (new or inside merge)

- Append deduped items; update `trace`.
- Optionally trim to **max total evidence** (keep highest relevance or round-robin by source) to protect LLM context limits.

### 5.5 Loop back to `critical_analyst`

- Increment `research_round` after a successful follow-up merge.
- **Do not** re-run `planner` from scratch unless you add an explicit “full replan” mode (Phase 2 can skip this).

### 5.6 `insight_generator` / `report_builder`

- Extend prompts slightly so the final report includes a short **“Research passes”** or **“Follow-up retrieval”** subsection when `research_round > 1`.
- Ensure contradictions and gaps from the **last** analyst pass are what insights use.

---

## 6. Configuration (`deep_researcher/config.py` + `app.py`)

| Setting | Default suggestion | Notes |
|---------|-------------------|--------|
| `MAX_RESEARCH_ROUNDS` | `1` | Ship default = current behavior. |
| `MAX_FOLLOWUP_QUERIES` | `6` | Cap JSON size and API calls. |
| `MAX_EVIDENCE_ITEMS` | tunable | After merge, truncate with logged warning. |

Wire **`max_research_rounds`** (and any user-facing caps you expose) in **`app.py` in the same milestone** as state + graph support—see §3.1.

---

## 7. Implementation Checklist

Use this as execution order; **interleave** UI rows with backend rows in the same milestone where possible.

1. **Models:** Extend `ResearchState` and defaults in `run_research` / `graph.invoke` initial state.
2. **Config:** Add env or `Settings` fields for max rounds, max follow-up queries, max evidence.
3. **UI (M1):** Add Gradio control(s) for `max_research_rounds` (and pass through to `initial_state`); optional layout shell (tabs / columns) so later panels do not require restructuring.
4. **gap_planner node:** Implement LLM call + JSON parse + fallback (similar to `planner_node`).
5. **Conditional routing:** Wire `should_continue` in `build_graph`; verify LangGraph compile and single-pass still runs with `max_research_rounds=1`.
6. **Follow-up retrieval:** Gate parallel retrievers by `followup_tools` and `followup_queries`; merge with dedupe.
7. **UI (M2):** Return `gap_findings` (and optionally last `followup_queries`) from `run_research`; render **Gaps / follow-up** markdown; enrich trace display with round labels.
8. **Analyst context:** Optionally pass **more items** in later rounds or **prioritize** items from latest round (document choice).
9. **Report:** Mention multi-pass in narrative when applicable.
10. **UI (M3):** **Sources** vs **Report** separation; evidence table with excerpt column or side panel; default visibility for detailed extracts per §3.1.
11. **Tests:** Add a minimal test or script that mocks LLM for `gap_planner` and asserts graph routing (optional but valuable).
12. **Docs:** Update [ARCHITECTURE.md](./ARCHITECTURE.md) (graph + UI); update [SETUP.md](./SETUP.md) / [README.md](./README.md) for new controls.

---

## 8. Acceptance Criteria

- With `max_research_rounds=1`, output and behavior are **substantially unchanged** (regression check).
- With `max_research_rounds=2` and a question designed to expose gaps, `trace` shows **two** analyst passes and **non-empty** follow-up retrieval when the gap planner proposes queries.
- Deduped `evidence` does not explode duplicate URLs across rounds.
- Run completes within configurable bounds (no infinite loop).
- **UI:** Users can set research rounds from the UI; multi-pass runs surface **gaps and/or follow-up queries** and a **clearer sources/report layout** without requiring a second UI project phase.

---

## 9. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Latency doubles or triples | Cap rounds at 2–3; cap queries per round; optional “fast mode” (rounds=1). |
| LLM invents useless follow-up queries | Structured JSON + empty-query exit; optional heuristic: skip if queries overlap Jaccard with previous `queries`. |
| Context overflow | `MAX_EVIDENCE_ITEMS` + analyst sampling strategy; optional summarization of older evidence (future phase). |
| Cost (API + Tavily) | Tool allowlist; respect `enable_web_search`; log per-round usage in `retrieval_log`. |

---

## 10. Out of Scope (Phase 2)

- **Full conversational chat** (multi-turn Q&A on the report, “expand section 3”)—**Phase 3**; Phase 2 may still add **read-only** gap/trace panels.
- **Fetching full pages** or PDFs from arbitrary URLs (security and scope).
- **Automated fact verification** against full text.
- **Persistent multi-user sessions** and databases.
- Changing **Tavily / arXiv / Wikipedia** client libraries beyond what follow-up queries require.

---

## 11. Suggested Milestones

Each milestone includes **both** backend and UI so work is not duplicated across a “logic phase” and a “UI phase.”

| Milestone | Backend deliverable | UI deliverable (same milestone) |
|-----------|---------------------|----------------------------------|
| **M1** | State + config + `max_research_rounds=1` default; graph compiles and runs unchanged path. | **Research rounds** control wired to `initial_state`; optional **tabs/columns** scaffold for report vs sources. |
| **M2** | `gap_planner` + conditional edge + one follow-up loop; `gap_findings` / follow-up queries in state or return payload. | **Gaps / follow-up** markdown panel; trace area shows **round** or multi-pass steps (not buried-only). |
| **M3** | Dedupe, evidence cap, trace/report prompt updates for multi-pass. | **Sources** tab/column with excerpts; reduce reliance on a single hidden “Detailed Analysis” toggle for primary review. |
| **M4** | — | **Docs:** ARCHITECTURE.md (graph + UI), SETUP/README for new controls. |

---

*Last updated: Phase 2 includes parallel UI track (vertical slices with orchestration) to avoid repeated UI/integration work.*
