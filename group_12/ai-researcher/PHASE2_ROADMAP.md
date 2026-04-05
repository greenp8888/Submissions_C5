# Phase 2 Roadmap: Multi-Pass Deep Research

This document describes **Phase 2** of evolving the Local Multi-Agent Deep Researcher from a **single-pass** LangGraph pipeline into a **multi-pass** workflow: detect gaps, refine queries, retrieve again, merge evidence, and re-synthesize—without requiring the user to manually re-run the full job.

**Scope:** Orchestration and state only. Interactive chat, UI overhaul, and full URL-fetch verification are **out of scope** for Phase 2 (see [Out of scope](#out-of-scope)).

**Related docs:** [ARCHITECTURE.md](./ARCHITECTURE.md) (current single-pass design), [FUNCTIONAL.md](./FUNCTIONAL.md) if present.

---

## 1. Objectives

1. **Closed-loop retrieval:** After an initial retrieve → analyze pass, the system identifies **what is still missing** or **under-supported** and issues **targeted follow-up retrieval**.
2. **Bounded cost and latency:** Multi-pass behavior must be **capped** (max rounds, max new queries, max evidence growth) and **configurable**.
3. **Traceability:** Each pass is visible in `trace` / `retrieval_log` so demos and debugging stay understandable.
4. **Backward compatibility:** A **“single pass”** mode (max rounds = 1) preserves today’s behavior for quick runs and tests.

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

## 6. Configuration (`deep_researcher/config.py` + UI later)

| Setting | Default suggestion | Notes |
|---------|-------------------|--------|
| `MAX_RESEARCH_ROUNDS` | `1` | Ship default = current behavior. |
| `MAX_FOLLOWUP_QUERIES` | `6` | Cap JSON size and API calls. |
| `MAX_EVIDENCE_ITEMS` | tunable | After merge, truncate with logged warning. |

Expose `max_research_rounds` in `app.py` (slider 1–3) in a **small follow-up PR** after core graph works.

---

## 7. Implementation Checklist

Use this as execution order; check off in PRs.

1. **Models:** Extend `ResearchState` and defaults in `run_research` / `graph.invoke` initial state.
2. **Config:** Add env or `Settings` fields for max rounds, max follow-up queries, max evidence.
3. **gap_planner node:** Implement LLM call + JSON parse + fallback (similar to `planner_node`).
4. **Conditional routing:** Wire `should_continue` in `build_graph`; verify LangGraph compile and single-pass still runs with `max_research_rounds=1`.
5. **Follow-up retrieval:** Gate parallel retrievers by `followup_tools` and `followup_queries`; merge with dedupe.
6. **Analyst context:** Optionally pass **more items** in later rounds or **prioritize** items from latest round (document choice).
7. **Report:** Mention multi-pass in narrative when applicable.
8. **Tests:** Add a minimal test or script that mocks LLM for `gap_planner` and asserts graph routing (optional but valuable).
9. **Docs:** Update [ARCHITECTURE.md](./ARCHITECTURE.md) section on the graph with the new diagram and state fields.

---

## 8. Acceptance Criteria

- With `max_research_rounds=1`, output and behavior are **substantially unchanged** (regression check).
- With `max_research_rounds=2` and a question designed to expose gaps, `trace` shows **two** analyst passes and **non-empty** follow-up retrieval when the gap planner proposes queries.
- Deduped `evidence` does not explode duplicate URLs across rounds.
- Run completes within configurable bounds (no infinite loop).

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

- **Chat UI** and section-level “expand this” (Phase 3).
- **Fetching full pages** or PDFs from arbitrary URLs (security and scope).
- **Automated fact verification** against full text.
- **Persistent multi-user sessions** and databases.
- Changing **Tavily / arXiv / Wikipedia** client libraries beyond what follow-up queries require.

---

## 11. Suggested Milestones

| Milestone | Deliverable |
|-----------|-------------|
| M1 | State + config + `max_research_rounds=1` default; graph still compiles and runs. |
| M2 | `gap_planner` + conditional edge + one follow-up loop (round 2 only). |
| M3 | Dedupe, evidence cap, trace/report updates, Gradio slider for rounds. |
| M4 | ARCHITECTURE.md + manual test notes in SETUP or README. |

---

*Last updated: aligned with codebase under `deep_researcher/` (LangGraph linear flow + parallel retrieval merge).*
