# Feature: See Where Sources Disagree

This document describes the implementation of **cross-source contradiction surfacing**, **credibility-weighted reasoning**, and a **Contested Claims (Low Consensus)** view in the AI Hackathon Deep Researcher.

## User goals

- Surface **where sources contradict** each other (not only a single synthesized answer).
- Show **“Source A says X, Source B says Y”** style highlights in context.
- Explain **which side the system weights more** and **why**, using the existing credibility pipeline.
- Provide a dedicated section for claims with **low consensus** so users do not over-trust one-sided or unstable evidence.

## Summary of behavior

1. After claims are derived from findings, the **contradiction checker** compares claim pairs (heuristic overlap + tension signals).
2. For each detected disagreement, a **`Contradiction`** record stores both positions, source labels, optional claim IDs, a **heuristic lean** (`a` / `b` / `tie`), and **credibility reasoning** grounded in per-source scores and explanations.
3. **Claims** involved in disagreements get updated **`consensus_pct`**, **`contradicting_source_ids`**, **`contested`**, and adjusted **trust**.
4. The **report builder** adds inline callouts under detailed findings, a **“Where Sources Disagree”** section, and **“Contested Claims (Low Consensus)”**.
5. The **Gradio UI** exposes **consensus %** and **contested** in the claims table and augments the confidence summary.

## Data model changes

**File:** `src/ai_app/schemas/research.py`

### `Claim`

| Field | Type | Purpose |
|--------|------|--------|
| `consensus_pct` | `int` (default `100`) | Higher when sources align; reduced when the claim participates in detected disagreements or related heuristics. |

### `Contradiction`

| Field | Type | Purpose |
|--------|------|--------|
| `claim_a_id`, `claim_b_id` | `str` | Links back to `Claim.id` for reporting and metadata updates. |
| `source_a_label`, `source_b_label` | `str` | Human-readable names (filename/title + provider). |
| `position_a`, `position_b` | `str` | Truncated statement text (“says …”). |
| `more_credible_side` | `str` | `"a"`, `"b"`, or `"tie"` from comparing primary supporting sources’ `credibility_score`. |
| `credibility_reasoning` | `str` | Narrative combining scores and optional `credibility_explanation` from sources. |
| `consensus_score` | `float \| None` | Heuristic similarity between the two statements (how stark the textual split is). |

Existing fields (`claim_a`, `claim_b`, `source_a_id`, `source_b_id`, `analysis`, `resolution`) are retained for compatibility and narrative context.

## Agents and orchestration

### `ContradictionCheckerAgent`

**File:** `src/ai_app/agents/contradiction_checker_agent.py`

- **Input:** `claims: list[Claim]`, `sources: list[Source]`.
- **Pairing:** For each unordered claim pair, applies heuristics:
  - Opposing polarity terms (e.g. increase/decrease, benefit/harm).
  - Negation / dispute markers with sufficient topical overlap.
  - Uncertainty language vs clearer conflicting text, with overlap and similarity gates.
  - High topic overlap (token Jaccard) but low full-string similarity.
- **Output:** Up to 24 `Contradiction` objects with labels, positions, lean, and reasoning.
- **Credibility lean:** Compares credibility of each side’s **primary** supporting source (`supporting_source_ids[0]`). Near-equal scores yield **`tie`**.

### `CriticalAnalysisAgent`

**File:** `src/ai_app/agents/critical_analysis_agent.py`

- Invokes `ContradictionCheckerAgent.run(claims, session.sources)` (no longer `run(claims)` only).
- **`_apply_contradiction_metadata`**:
  - Cross-links **contradicting** source IDs between paired claims.
  - Marks involved claims **contested**, recomputes **`consensus_pct`**, and applies a **trust** penalty scaled by involvement.
  - Preserves handling for keyword-**contested** findings when no pairwise row exists (caps consensus).

**Removed:** Incorrect assignment `contradicting_source_ids = supporting_source_ids[:1]` for contested claims.

### `ReportBuilderAgent`

**File:** `src/ai_app/agents/report_builder_agent.py`

- Builds a map from **claim id → contradictions** for inline notes.
- **Detailed Findings:** Adds **Consensus %** per claim and, where applicable, **Where sources disagree** + **Credibility read** blocks.
- **New / renamed sections:**
  - **`Where Sources Disagree`** (`section_type`: `disagreements`) — structured A vs B pairs with tension, lean, and reasoning.
  - **`Contested Claims (Low Consensus)`** (`section_type`: `contested_claims`) — claims with `consensus_pct < 60` or contested with `consensus_pct < 72`, capped for length, with citations and tension sources.
- Report section **order** shifts: appendix is now order `13` (previously `12`); intermediate sections renumbered.

Exports (Markdown/PDF) use `ReportService.render_markdown(session)` and therefore include these sections automatically.

## UI changes

| Location | Change |
|----------|--------|
| `ui/components/evidence_table.py` | Claim rows include **Consensus %** and **Contested** (`yes`/`no`). |
| `ui/gradio/deep_researcher.py` | Dataframe headers extended to nine columns to match the table. |
| `ui/components/confidence_badge.py` | Summary adds **average source consensus** and **count of contested claims**. |

## Limitations and expectations

- Detection is **heuristic**, not LLM-judged: it depends on claim wording and overlap. Sparse or paraphrased opposites may be missed.
- Each side’s “primary” source is the **first** ID in `supporting_source_ids`; richer multi-source voting is future work.
- **Tie** means similar credibility scores, not epistemic equality—users should still read both excerpts.

## Files touched (reference)

| File | Role |
|------|------|
| `src/ai_app/schemas/research.py` | `Claim.consensus_pct`, extended `Contradiction`. |
| `src/ai_app/agents/contradiction_checker_agent.py` | Pairwise detection and enrichment. |
| `src/ai_app/agents/critical_analysis_agent.py` | Wiring + `_apply_contradiction_metadata`. |
| `src/ai_app/agents/report_builder_agent.py` | Report sections and inline highlights. |
| `ui/components/evidence_table.py` | Table columns. |
| `ui/gradio/deep_researcher.py` | Dataframe headers. |
| `ui/components/confidence_badge.py` | Aggregate consensus / contested stats. |

## Related product docs

- High-level design and flows: `Group_9/HLD.md` (orchestration and trust themes).
- Runnable app overview: `README.md` in this repository.
