# LangGraph topology (current implementation)

This document reflects **`build_graph()`** in [`deep_researcher/graph.py`](./deep_researcher/graph.py): nodes, edges, and routing. For product context see [ARCHITECTURE.md](./ARCHITECTURE.md).

**Human-in-the-loop review** (upload digest + LLM alignment, then **Yes / No** before research runs) lives in **Gradio** only: [`app.py`](./app.py) (`run_preflight_review`, `confirm_yes` → `run_research_after_confirm` → `graph.invoke`). It is **not** a LangGraph node, interrupt, or checkpoint, so it does **not** appear on the compiled graph PNG below. For the **full** product flow including that step, see [§0](#0-full-application-flow-gradio--langgraph) and [`docs/images/application_flow_with_hitl.png`](./docs/images/application_flow_with_hitl.png).

---

## 0. Full application flow (Gradio + LangGraph)

```mermaid
flowchart TB
    subgraph hitl["Gradio UI — human-in-the-loop (outside LangGraph)"]
        direction TB
        U[User: question + optional files]
        R[1. Review uploads & question]
        PF[preflight_llm: digest + alignment vs question]
        H{{2. Human: Yes run research / No cancel}}
        U --> R
        R --> PF
        PF --> H
        H -->|No — cancel| U
    end

    H -->|Yes — run full research| INV["app.py: graph.invoke(initial_state)"]

    subgraph lg["LangGraph StateGraph — detail in §1 and langgraph_topology.png"]
        direction TB
        INV --> ST([__start__])
        ST --> P[planner → retrieval → analyst → …]
        P --> EN([__end__])
    end

    EN --> OUT[Report, sources, trace in UI]
```

![Application flow — Gradio preflight then LangGraph](./docs/images/application_flow_with_hitl.png)

_Source: [`docs/images/application_flow_with_hitl.mmd`](./docs/images/application_flow_with_hitl.mmd)._

---

**LangGraph-only PNG** (matches the compiled `StateGraph` exactly — no UI steps):

![LangGraph topology — Phase 2 deep researcher](./docs/images/langgraph_topology.png)

_Authoritative source: [`docs/images/langgraph_topology_compiled.mmd`](./docs/images/langgraph_topology_compiled.mmd) (from `build_graph().get_graph().draw_mermaid()`). **Regenerate everything:**_

```bash
python scripts/export_langgraph_mermaid.py
cd docs/images && npx -y @mermaid-js/mermaid-cli -i langgraph_topology_compiled.mmd -o langgraph_topology.png -w 3600 -H 2800 -b white
```

_(Mermaid CLI needs a local Chrome/Chromium for Puppeteer.) For a hand-drawn flow with subgraphs, see [`docs/images/langgraph_topology.mmd`](./docs/images/langgraph_topology.mmd) (logical layout only; keep in sync with [`deep_researcher/graph.py`](./deep_researcher/graph.py))._

---

## 1. End-to-end flow (logical)

```mermaid
flowchart TB
    START([START]) --> planner[planner]
    planner --> prep[prep_retrieval]

    subgraph wave1["Initial retrieval (parallel)"]
        prep --> L[local_media_retriever]
        prep --> W[wikipedia_retriever]
        prep --> A[arxiv_retriever]
        prep --> T[tavily_retriever]
        L --> M1[retriever_merge]
        W --> M1
        A --> M1
        T --> M1
    end

    M1 --> CA[critical_analyst]

    CA -->|max_research_rounds ≤ 1| ID[insight_direct]
    CA -->|max_research_rounds ≥ 2 and analyst_pass < max| GP[gap_planner]

    GP -->|no followup_queries| IGS[insight_post_gap_skip]
    GP -->|has followup_queries| PF[prep_followup]

    subgraph wave2["Follow-up retrieval (parallel, optional)"]
        PF --> Lf[local_media_retriever_f]
        PF --> Wf[wikipedia_retriever_f]
        PF --> Af[arxiv_retriever_f]
        PF --> Tf[tavily_retriever_f]
        Lf --> M2[retriever_merge_followup]
        Wf --> M2
        Af --> M2
        Tf --> M2
    end

    M2 --> CAF[critical_analyst_followup]
    CAF --> IPF[insight_post_followup]

    ID --> RD[report_direct]
    IGS --> RGS[report_post_gap_skip]
    IPF --> RPF[report_post_followup]

    RD --> END([END])
    RGS --> END
    RPF --> END
```

> **Note:** `route_after_analyst` / `route_after_gap` use numeric rules (see §3); the diagram labels summarize them. **`max_research_rounds` is clamped to 1–2** in routing.

---

## 2. Parallel fan-out / fan-in (structural)

Two **independent** retrieve→merge pipelines share **no** retriever or merge nodes, so LangGraph never waits on a merge that did not run.

```mermaid
flowchart LR
    subgraph initial["Pipeline A — first wave"]
        direction TB
        PR(prep_retrieval) --> R1{{4 retrievers}}
        R1 --> M(retriever_merge)
    end

    subgraph follow["Pipeline B — follow-up wave"]
        direction TB
        PF(prep_followup) --> R2{{4 × *_f retrievers}}
        R2 --> MF(retriever_merge_followup)
    end

    M --> CA[critical_analyst]
    MF --> CAF[critical_analyst_followup]
```

---

## 3. Routing functions

| Source node | Routing function | Target | Condition (simplified) |
|-------------|------------------|--------|-------------------------|
| `critical_analyst` | `route_after_analyst` | `insight_direct` | `max_research_rounds ≤ 1` **or** `analyst_pass_count ≥ max_research_rounds` |
| `critical_analyst` | `route_after_analyst` | `gap_planner` | else (typically `max_research_rounds = 2` and first pass complete) |
| `gap_planner` | `route_after_gap` | `insight_post_gap_skip` | `analyst_pass_count ≥ max_research_rounds` **or** empty `followup_queries` |
| `gap_planner` | `route_after_gap` | `prep_followup` | non-empty `followup_queries` and passes still below max |

`critical_analyst_followup` has **no** conditional: it always goes to `insight_post_followup` (second pass is terminal for the supported 2-pass design).

---

## 4. Why duplicate `insight_*` / `report_*` nodes?

LangGraph joins nodes with **multiple incoming edges** by waiting for **all** parents. A single shared `insight_generator` fed from three branches would deadlock. The implementation uses **three parallel chains** to `END`:

```mermaid
flowchart LR
    ID[insight_direct] --> RD[report_direct] --> END([END])
    IGS[insight_post_gap_skip] --> RGS[report_post_gap_skip] --> END
    IPF[insight_post_followup] --> RPF[report_post_followup] --> END
```

Each chain runs **`insight_node` / `report_node`** with the same implementation; only the graph **node id** differs.

---

## 5. Node responsibilities (quick reference)

| Node | Role |
|------|------|
| `planner` | LLM → `subquestions`, `research_objective` |
| `prep_retrieval` | `queries` = question + subquestions; clears `retrieval_tool_filter` |
| `*_retriever` | Channel-specific evidence (respects `retrieval_tool_filter` on follow-up) |
| `retriever_merge` | Replace corpus with first-wave batch (trim to `max_evidence_items`) |
| `retriever_merge_followup` | Append + dedupe follow-up batch |
| `critical_analyst` / `critical_analyst_followup` | LLM critique; increments `analyst_pass_count` |
| `gap_planner` | LLM → `followup_queries`, `followup_tools`, `gap_round_log` |
| `prep_followup` | Cap queries; set `retrieval_tool_filter` |
| `insight_*` | LLM → `insights` |
| `report_*` | LLM narrative + citation catalog; per-tool appendix LLM; assemble `final_report` |

---

## 6. Rendering diagrams

- **LangGraph PNG:** [`docs/images/langgraph_topology.png`](./docs/images/langgraph_topology.png) (from [`langgraph_topology_compiled.mmd`](./docs/images/langgraph_topology_compiled.mmd); regenerate via [`scripts/export_langgraph_mermaid.py`](./scripts/export_langgraph_mermaid.py) + mermaid-cli as in the figure note).
- **Gradio + LangGraph (HITL) PNG:** [`docs/images/application_flow_with_hitl.png`](./docs/images/application_flow_with_hitl.png) from [`application_flow_with_hitl.mmd`](./docs/images/application_flow_with_hitl.mmd): `cd docs/images && npx -y @mermaid-js/mermaid-cli -i application_flow_with_hitl.mmd -o application_flow_with_hitl.png -w 3200 -H 1800 -b white`
- **GitHub / GitLab:** Mermaid renders in Markdown preview.
- **VS Code:** “Markdown Preview Mermaid Support” or similar extension.
- **Export PNG/SVG:** [Mermaid Live Editor](https://mermaid.live) (paste the fenced blocks) or **@mermaid-js/mermaid-cli** as in the note under the figure above.

---

*Generated to match the Phase 2 graph as implemented in `deep_researcher/graph.py`.*
