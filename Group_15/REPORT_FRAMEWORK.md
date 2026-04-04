# Traction Scanner — Report Framework

## Purpose

This document defines the output structure, scoring logic, and content strategy for the traction scanner report. It serves as the specification for the **Report Writing Agent** node in the LangGraph pipeline.

The report answers one question: **"Should I build this, and if so, where's my opening?"**

---

## Design Principles

### Who reads this

A startup founder with a product idea who needs to make a build/pivot/kill decision. They have 2-3 minutes for the first pass, 10 minutes if they're interested.

### What research says works

- YC/a16z care about: Is the problem urgent? Is demand real (not stated)? Who are the substitutes? Where's the unfair advantage?
- Founders consistently skip: TAM/SAM/SOM, feature matrices, SWOT, methodology sections
- The highest-value signal: **switching intent posts** ("I'm leaving X because...") — tells you what to build, who the customer is, and that they've already decided to move
- The difference between "so what" and "aha": every section leads with interpretation, follows with evidence. Raw data without a verdict is noise.

### Scoring philosophy

- Score at **section level**, not a single overall score (0-100 composites collapse useful signal)
- Use **minimum-gating**, not averaging: one red critical dimension prevents a green overall, even if everything else is strong
- **Gray/unknown is valid** — insufficient data is not the same as bad data
- Every score chip must show the rule that triggered it (tooltip or inline)
- Show **trend direction** (improving/declining arrow) alongside status

---

## Data Sources

| Source | What It Provides | Agent Tool |
|---|---|---|
| **GitHub API** | Repo metrics, fork velocity, issues, PRs, contributors, dependency count | REST + GraphQL + web scrape |
| **Reddit API** | Discussion volume, sentiment, switching intent, pain points | AsyncPRAW + PullPush |
| **Product Hunt API** | Launch reception, vote counts, comments, maker track record | GraphQL via httpx |
| **Perplexity** | Real-time web intelligence, trend synthesis, funding signals, news | MCP (`perplexity_search`, `perplexity_research`, `perplexity_reason`) |
| **Hacker News** | Developer sentiment, technical discussion, launch reception | Algolia HN Search API |

### Perplexity Integration

Perplexity fills a critical gap the other sources can't: **synthesized web intelligence** across sources we don't scrape directly (blogs, news, funding databases, Twitter/X, Discord, Indie Hackers, G2/Capterra reviews).

**Use Perplexity for:**
- "What's the latest news/funding activity around [competitor]?"
- "What do developers think about [product category]?" (synthesizes across forums we don't scrape)
- "Are there any recent pivots or shutdowns in this space?"
- "What pricing models are competitors using?"
- Trend validation — cross-check Reddit/GitHub signals against broader web

**LangGraph tool pattern:**
```python
# Quick factual lookup
perplexity_ask(query="What is [product] and who founded it?")

# Broad web search for market context
perplexity_search(query="[product category] market trends 2026")

# Deep research synthesis
perplexity_research(research_query="competitive landscape for [product category] including recent funding, pricing, and developer adoption")

# Complex reasoning over evidence
perplexity_reason(problem="Given these GitHub and Reddit signals, is this market opportunity real or hype?")
```

**Where Perplexity output appears in the report:**
- Section 0 (Verdict): Cross-validated market context
- Section 2 (Competitive Landscape): Funding signals, pricing intel, recent news
- Section 4 (Momentum): Trend validation against broader web
- Section 5 (Counter-Arguments): Steelman objection synthesis

---

## Report Structure

Seven sections. Designed to be scanned in 2-3 minutes with full expandability. Each section earns its place by answering a specific founder question.

---

### Section 0: The Verdict

**Founder question:** "Give me the bottom line."

**Content:**
- One-sentence verdict: `"Build with differentiation focus"` / `"Strong entry signal — market is fragmented"` / `"Market appears saturated — consider pivoting angle"`
- Three signal chips (labeled, not just colors):

```
[Demand: STRONG ↑]  [Competition: FRAGMENTED →]  [Gap: IDENTIFIED ✓]
```

- One key risk line: `"Main risk: [competitor X] has 5k stars + active Discord — community lock-in is real"`
- Data freshness indicator: `"Based on data from last 90 days across 3 sources"`

**Scoring logic:**
- Verdict is LLM-synthesized (not rule-based) — the Report Writing Agent reads all section scores and evidence, then writes the verdict
- The three chips are derived from section-level scores (Demand from Section 1, Competition from Section 2, Gap from Section 3)
- The risk line is extracted from Section 5 (Counter-Arguments)

**Why it earns its place:** The only section guaranteed to be read. Every other section justifies or challenges what's here. 90-second founders stop here. 10-minute founders use it as navigation anchor.

---

### Section 1: Demand Signal

**Founder question:** "Is demand real or just noise?"

**Signal chip:** `STRONG` / `MODERATE` / `WEAK` / `INSUFFICIENT DATA`

**Content structure:**

```
## Demand Signal [STRONG ↑]

**Interpretation:** Growing developer interest with 3x Reddit discussion 
increase in 6 months. Multiple "would pay for this" signals detected.

### Evidence

| Source | Metric | Value | Trend |
|--------|--------|-------|-------|
| Reddit | Posts mentioning category (6mo) | 47 | ↑ 3.2x vs prior 6mo |
| Reddit | Switching intent threads | 8 | High signal |
| GitHub | Open issues tagged "enhancement" (top 5 repos) | 312 | ↑ steady |
| GitHub | Thumbs-up on feature requests (top 10) | 1,247 total | Concentrated demand |
| Product Hunt | Launches in category (12mo) | 6 | Growing |
| Perplexity | Recent articles/mentions | "[category] trending in dev communities" | Confirmed |

### Top Demand Signals (verbatim)

> "We've been looking for exactly this — spent 3 months building an internal 
> tool that does 20% of what's needed" — r/devtools, 42 upvotes

> "Would pay $50/month for something that actually works here" 
> — r/SaaS, 28 upvotes

> Issue #342 on [repo]: "Please add [feature X]" — 89 👍 reactions

### Expand: Full evidence list →
[Collapsed: all Reddit posts, GitHub issues, PH launches with links]
```

**Scoring thresholds:**

| Score | Criteria |
|---|---|
| STRONG | Reddit mentions growing >50% MoM OR >20 posts in 6mo + GitHub issue demand (>50 total thumbs-up on enhancement requests) + PH launches exist |
| MODERATE | Reddit mentions exist (5-20 in 6mo) + some GitHub issue demand + at least 1 PH launch |
| WEAK | <5 Reddit mentions + low GitHub issue demand + no PH launches |
| INSUFFICIENT DATA | <3 total data points across all sources |

**Key design choice:** Lead with trend direction, not absolute volume. 50 posts/month growing 40% MoM > 500 posts/month flat for 2 years.

---

### Section 2: Competitive Landscape

**Founder question:** "Who else is doing this and how are they doing?"

**Signal chip:** `DOMINATED` / `CROWDED` / `FRAGMENTED` / `EMERGING` / `WHITESPACE`

**Content structure:**

```
## Competitive Landscape [FRAGMENTED →]

**Interpretation:** 5 active projects, none dominant. Largest has 1,300 stars 
with narrow focus. No single product covers the full job-to-be-done.

### Competitor Table

| Product | GitHub ★ | Activity | PH Votes | Last Commit | License | Signal |
|---------|----------|----------|----------|-------------|---------|--------|
| cursorless | 1,300 | 🟢 Active | — | yesterday | MIT | Niche leader |
| n8n-wf-builder | 506 | 🟢 Active | — | 2 weeks ago | MIT | Rising fast |
| open-interpreter | 63,000 | 🟡 Moderate | 2,100 | 3 months ago | AGPL | Category giant |
| voqal | 190 | 🔴 Stalled | — | 15 months ago | Apache | Abandoned |
| caster | 352 | 🟢 Active | — | 1 week ago | GPL | Legacy tool |

### Concentration

No single player holds >40% of community attention. The market is 
fragmented across 3 sub-segments with different user bases.

### Funding & News (via Perplexity)

- Open Interpreter raised $X in [date] — focus on [direction]
- No recent acquisitions in the voice-to-code space
- [Competitor] recently announced [feature] — potential threat

### Expand: Full repo profiles →
[Collapsed: detailed per-repo traction profiles with all metrics]
```

**Scoring thresholds:**

| Score | Criteria |
|---|---|
| DOMINATED | 1 repo with >10x stars of nearest competitor + active maintenance |
| CROWDED | 4+ active repos, 2+ with >1k stars, healthy commit velocity across all |
| FRAGMENTED | 3+ repos but none dominant, different focus areas, mixed activity levels |
| EMERGING | 1-2 repos with <500 stars, early stage, growing |
| WHITESPACE | 0 active repos directly addressing the idea; only adjacent solutions exist |

**Key design choice:** Show activity signals, not feature matrices. A repo with 2k stars and no commits in 8 months is an OPPORTUNITY. A repo with 500 stars and 50 commits/month is a THREAT. The table must surface this distinction.

---

### Section 3: The Gap

**Founder question:** "Where's the opening I can exploit?"

**Signal chip:** `CLEAR GAP` / `PARTIAL GAP` / `NO CLEAR GAP`

**This is the most valuable section.** It's where the "aha" moment lives.

**Content structure:**

```
## The Gap [CLEAR GAP ✓]

**Interpretation:** Users consistently ask for voice-to-specification 
(not just voice-to-text). No existing product does clarification 
+ structuring + generation as a pipeline. The gap is at the 
specification layer, not the execution layer.

### Top Unmet Needs (ranked by signal strength)

1. **Voice-to-specification, not just voice-to-prompt** (Signal: 4/5)
   - GitHub: 89 👍 on cursorless issue requesting "higher-level actions"
   - Reddit: "Voice coding should focus on refactoring, not dictation" — HN, 2020 (still unbuilt)
   - Perplexity: No product launched in this specific sub-category

2. **Cross-session memory for voice-directed projects** (Signal: 3/5)
   - Reddit: "The model forgot what the app was supposed to do" — 4,753 related posts
   - GitHub: Context loss is #1 complaint across vibe-coding repos

3. **Custom vocabulary that learns the codebase** (Signal: 3/5)
   - HN: "Voice tools misrecognize library names" — repeated across 3 threads
   - PH: Claude Code Voice Mode dismissed as "just dictation"

### Switching Intent (verbatim — highest-value signals)

> "I tried Talon but it's too low-level — I want to describe WHAT 
> I want, not HOW to edit" — r/devtools

> "Moved away from Copilot Voice because it doesn't understand 
> my project context" — r/LocalLLaMA

### What Exists vs. What's Missing

| Layer | Exists | Missing |
|-------|--------|---------|
| Speech-to-text | Whisper, Deepgram | Codebase-aware vocabulary |
| Voice commands | Cursorless + Talon | Only structural editing |
| NL-to-workflow | n8n-builder, Open Interpreter | Text-only, no voice-native |
| Voice-to-specification | **Nobody** | **The core gap** |

### Expand: All evidence →
```

**Scoring thresholds:**

| Score | Criteria |
|---|---|
| CLEAR GAP | 3+ distinct unmet needs identified with evidence from 2+ sources each; switching intent posts exist |
| PARTIAL GAP | 1-2 unmet needs with evidence; some switching intent but limited |
| NO CLEAR GAP | Existing products cover the job well; complaints are about execution, not missing capabilities |

**Key design choice:** Show actual quotes. Do not paraphrase. The raw voice of a frustrated user is more persuasive than any score.

---

### Section 4: Momentum Check

**Founder question:** "Is this market heating up or cooling down? Is now the right time?"

**Signal chip:** `ACCELERATING` / `STABLE` / `DECLINING`

**Content structure:**

```
## Momentum [ACCELERATING ↑]

**Interpretation:** Discussion volume doubled in Q1 2026. Two new PH 
launches in the last 3 months. GitHub activity across the space is 
at a 12-month high. Market is entering growth phase.

### Timeline

| Period | Reddit Posts | GitHub Stars (top 5) | PH Launches | Notable Events |
|--------|-------------|---------------------|-------------|----------------|
| Q2 2025 | 12 | +800 | 1 | Voqal goes quiet |
| Q3 2025 | 18 | +1,200 | 0 | — |
| Q4 2025 | 24 | +1,500 | 2 | CodeWords launches on PH |
| Q1 2026 | 47 | +2,100 | 3 | Claude Code Voice Mode, MCP wave |

### Recent Catalysts (via Perplexity)

- Claude Code Voice Mode launched April 2026 — validates the category but underwhelmed ("just dictation")
- MCP ecosystem growth driving n8n-workflow-builder adoption
- Andrej Karpathy publicly spending 16+ hrs/day directing agents in NL

### Expand: Full timeline data →
```

---

### Section 5: Counter-Arguments

**Founder question:** "What's the strongest case against building this?"

**No signal chip.** This section is pure narrative — the steelman objection.

**Content structure:**

```
## Counter-Arguments

**The strongest case against:**

"The voice-to-code market has a fundamental adoption ceiling. 
Power developers type faster than they speak structured commands. 
The addressable market may be limited to RSI/accessibility users 
(~2% of developers) plus a novelty-seeking early adopter tail 
that doesn't convert to paying customers."

### Specific Risks

1. **Community lock-in:** Cursorless + Talon have a deeply committed 
   user base (fork-to-star ratio 1.02). Switching them is hard.

2. **Voice UX is unproven at scale:** Voqal attempted this exact 
   product and stalled at 190 stars after 15 months. Why would 
   a new entrant succeed where they failed?

3. **The execution layer is commoditizing:** Open Interpreter (63k stars, 
   AGPL) may add voice as a feature, eliminating the standalone case.

### What would need to be true for this to work

- Voice-to-specification must be 3x faster than text-to-specification
- Custom vocabulary training must solve the "misrecognizes library names" problem
- Cross-session memory must work reliably (unsolved across all AI coding tools)
```

**Why it earns its place:** Every other section is subtly optimistic. This provides the counterweight. A report that only shows green is a cheerleader, not an analyst. This section is what separates an "aha" report from a "so what" report. It forces the founder to decide whether they can answer the objection.

**Implementation note:** This section requires LLM synthesis — Perplexity `reason` or the Report Writing Agent must read all evidence and produce the steelman objection. It cannot be assembled from raw data alone.

---

### Section 6: Repository Deep-Dives (collapsed by default)

**Founder question:** "Show me the details on each competitor."

**Content:** Per-repo traction profiles with the RED/ORANGE/GREEN scoring from the existing Python evaluator.

```
### cursorless-dev/cursorless [GREEN — GO FOR IT as a build-on-top target]

Score: 72/100

| Component | Score | Status |
|-----------|-------|--------|
| Fork activity | 38/100 | 🟡 Mixed |
| Comment health | 82/100 | 🟢 Strong |
| PR health | 71/100 | 🟢 Good |
| Update recency | 98/100 | 🟢 Very strong |
| Community sentiment | 68/100 | 🟢 Good |
| License (MIT) | 100/100 | 🟢 Permissive |

[Expand: raw metrics, debug info, Reddit mentions →]
```

This section reuses the existing scoring logic from [RED ORANGE GREEN-PY.md](RED%20ORANGE%20GREEN-PY.md) — the weighted formula (15% forks, 10% comments, 20% PRs, 20% recency, 25% sentiment, 10% license).

---

### Section 7: Sources & Methodology (collapsed by default)

**Founder question:** "Can I trust this data?"

**Content:**
- Full list of Reddit posts analyzed with permalinks
- Full list of GitHub repos with links
- Full list of PH launches with links
- Perplexity queries run and sources cited
- Search queries used per source
- Date range of data collection
- Data freshness per source

**Why it exists:** Credibility. Founders who distrust the verdict verify here. Collapsed by default — it's for the skeptic.

---

## Traffic Light (RAG) Scoring Rules

### Per-Section Scoring

Each section gets its own chip. The chips follow these rules:

| Color | Meaning | Display |
|---|---|---|
| 🟢 Green | Strong positive signal — supports building | `STRONG`, `CLEAR GAP`, `WHITESPACE`, `ACCELERATING` |
| 🟡 Orange | Mixed or moderate signal — proceed with caution | `MODERATE`, `PARTIAL GAP`, `FRAGMENTED`, `STABLE` |
| 🔴 Red | Negative signal — significant risk or blocker | `WEAK`, `NO CLEAR GAP`, `DOMINATED`, `DECLINING` |
| ⚪ Gray | Insufficient data — cannot assess | `INSUFFICIENT DATA` |

### Overall Verdict Logic

The verdict uses **minimum-gating**, not averaging:

```python
def compute_verdict(section_scores):
    # If ANY critical section is red, overall cannot be green
    critical_sections = ["demand", "competition", "gap"]
    
    if any(section_scores[s] == "RED" for s in critical_sections):
        return "CAUTION — significant risk detected"
    
    if all(section_scores[s] == "GREEN" for s in critical_sections):
        return "STRONG SIGNAL — market opportunity validated"
    
    # Mixed signals — most common case
    return "MIXED — opportunity exists with notable risks"
```

### Per-Repo Scoring (Section 6)

Reuses the existing weighted formula from the Python evaluator:

| Component | Weight | Source |
|---|---|---|
| Fork activity | 15% | `40 * log10(forks + 1)` |
| Comment health | 10% | Activity (50%) + response rate (50%) |
| PR health | 20% | Recent PRs (50%) + merge rate (50%) |
| Update recency | 20% | `100 - (days_since_update / 180) * 100` |
| Community sentiment | 25% | GitHub (70%) + Reddit (30%) blended |
| License | 10% | MIT/Apache=100, GPL=45, None=0 |

**Thresholds:**
- GREEN (≥70, recency ≥50, sentiment ≥60, license ≥45): "GO FOR IT"
- ORANGE (≥40): "HAS POTENTIAL, BUT RISKY"
- RED (<40 or no license or stale or toxic sentiment): "NOPE! LEAVE IT"

### Confidence Indicator

Every section chip includes a confidence level based on data coverage:

| Confidence | Criteria | Display |
|---|---|---|
| High | 10+ data points from 2+ sources | No qualifier |
| Medium | 5-9 data points OR single source | `(moderate confidence)` |
| Low | <5 data points | `(low confidence — limited data)` |

---

## LangGraph Agent Implementation

### Report Writing Agent Node

The Report Writing Agent is the final node in the LangGraph pipeline. It receives structured data from all retrieval agents and produces the formatted report.

**Input state:**
```python
{
    "idea_description": str,       # User's product idea
    "audience": str,               # Target audience
    "reference_products": list,    # Products/URLs the user mentioned
    
    # From retrieval agents:
    "github_data": {
        "repos": [...],            # Per-repo metrics and traction profiles
        "issue_signals": [...],    # Top feature requests by demand
        "dependency_counts": [...] # Inbound dependents per repo
    },
    "reddit_data": {
        "posts": [...],            # Relevant posts with scores
        "switching_intent": [...], # "Alternatives to X" threads
        "pain_points": [...],      # Frustration/complaint threads
        "comment_signals": [...]   # High-value comment patterns
    },
    "producthunt_data": {
        "launches": [...],         # Products in category with votes
        "comments": [...],         # Top PH comments with sentiment
        "maker_history": [...]     # Maker track records
    },
    "perplexity_data": {
        "market_context": str,     # Synthesized market overview
        "funding_signals": str,    # Recent funding/news
        "trend_analysis": str,     # Broader trend validation
        "counter_arguments": str   # Steelman objection
    },
    "hackernews_data": {
        "threads": [...],          # Relevant HN discussions
        "sentiment": str           # Developer sentiment summary
    }
}
```

**Output:** The formatted report as structured markdown following this framework.

### Agent Prompt Strategy

The Report Writing Agent should be prompted as:

```
You are a startup analyst writing a traction report for a founder 
evaluating whether to build a product. You have data from GitHub, 
Reddit, Product Hunt, Perplexity, and Hacker News.

Your job is to INTERPRET the data, not just present it. Every section 
must lead with your assessment, then show the evidence.

Rules:
1. Lead with the verdict — don't make the founder read 5 pages to 
   find out if the opportunity is real
2. Use actual quotes from Reddit/HN/PH — raw user voice > paraphrase
3. The Gap section is the most important — this is where the founder 
   finds their positioning
4. The Counter-Arguments section must be genuine — steelman the case 
   against building. If you can't find a real objection, say so
5. Score sections honestly — gray (insufficient data) > forced orange
6. Every claim must link to evidence in Section 7
```

---

## Mapping to User Stories

| Epic | Story | Report Section |
|---|---|---|
| EPIC 5 | US-5.1 Executive summary | Section 0: The Verdict |
| EPIC 5 | US-5.2 Feature comparison table | Section 2: Competitive Landscape (table) |
| EPIC 5 | US-5.3 Repo metadata report | Section 6: Repository Deep-Dives |
| EPIC 5 | US-5.4 Sentiment analysis | Section 1 (Reddit) + Section 6 (per-repo) |
| EPIC 5 | US-5.5 Traffic light scoring | All sections (per-section chips) + Section 6 (per-repo RAG) |
| EPIC 4 | US-4.3 Comparative analysis | Section 2 + Section 3 |
| EPIC 4 | US-4.4 Gap analysis | Section 3: The Gap |
| EPIC 3 | US-3.1 Matching algorithm | Section scores + verdict logic |

---

## Mapping to Flow Diagram

```
User Input          → Section 0 (idea context)
Query Analyzer      → Determines search queries for all sources
GitHub Retriever    → Section 2, 3, 4, 6
Reddit/HN Retriever → Section 1, 3, 4, 5
PH Retriever        → Section 1, 2, 4
Perplexity          → Section 0, 2, 4, 5
Requirements Matcher → Section 3 (gap = mismatch between user's idea and existing solutions)
Summarize           → Section-level interpretations
Analysis            → Section scores + verdict logic
Report              → Full formatted output per this framework
```

---

## Example: Minimal Viable Report (Hackathon Demo)

If you only have time for 3 sections, build these:

1. **Section 0: The Verdict** — one sentence + three chips + one risk. This IS the product.
2. **Section 3: The Gap** — verbatim user quotes showing unmet needs. This is the differentiator no other tool provides.
3. **Section 2: Competitive Landscape** — competitor table with activity signals. The visual anchor.

Everything else can be "Coming soon" in a demo. These three sections alone answer: "Is there a gap? Who's in the way? Should I go?"
