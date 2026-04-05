# PRD — AI Financial Coach Agent (2-day MVP)

**Status:** Draft  
**Owner:** TBD  
**Last updated:** April 4, 2026

---

## 1. Overview

A single-page web app that lets a user upload a bank statement CSV and instantly receive personalized financial analysis from four AI agents: a debt analyzer, a budget coach, a savings planner, and a debt payoff optimizer. Results surface in a live dashboard, and a chat interface lets the user ask follow-up questions grounded in their own data.

---

## 2. Problem statement

People struggle to get actionable, personalized financial advice without paying for a human advisor. Generic budgeting apps show charts but don't explain what to *do*. This app combines LLM reasoning with the user's actual transaction data to produce specific, prioritized recommendations in under a minute.

---

## 3. Goals

- Demonstrate a working multi-agent AI financial coach in a 2-day build
- Show value immediately on upload — no account creation, no manual data entry
- Produce recommendations specific enough to act on (not generic tips)
- Serve as a compelling demo of agent orchestration + LLM-powered data analysis

### Out of scope (this version)

- User accounts, auth, or persistent storage
- RAG / vector store (direct JSON injection used instead)
- Multi-month or multi-document analysis
- Mobile-optimized layout
- Real bank integrations (Plaid, etc.)
- What-if scenario modeling
- Proactive alerts or recurring analysis

---

## 4. Users

**Primary:** A single demo user (or evaluator) uploading their own or synthetic bank statement to see what the app produces. No sign-up required.

---

## 5. User flow

1. User lands on the app and sees a file upload prompt plus a "use demo data" button.
2. User uploads a CSV bank statement (or clicks demo data).
3. App parses the file and displays a loading state while all 4 agents run.
4. Dashboard renders with results across three panels.
5. User reads AI-generated recommendations in the insight feed.
6. User asks follow-up questions in the chat interface.

---

## 6. Features

### 6.1 Data ingestion

- Accept CSV upload (standard bank export format: date, description, amount, balance)
- Parse with PapaParse in the browser
- Normalize into a flat JSON schema: `{ transactions[], income[], debts[], summary{} }`
- Pre-loaded demo dataset ships with the app for zero-friction demos

**Acceptance criteria:**
- A standard Chase, Bank of America, or similar CSV parses without errors
- Demo data loads in under 1 second
- Malformed CSVs show a clear error message

---

### 6.2 Four AI agents

Each agent is a single Claude API call (`claude-sonnet-4-20250514`) with the user's financial JSON injected into the system prompt. Agents run sequentially. Each returns structured JSON that the UI renders.

#### Agent 1 — Debt analyzer
- Input: all transactions tagged as debt payments, plus any debt account data in the CSV
- Output: total debt, per-account balances, interest rate estimates, minimum payments, high-interest flags
- Key prompt instruction: identify and rank debts by urgency

#### Agent 2 — Budget coach
- Input: full transaction history, categorized by type (food, transport, subscriptions, etc.)
- Output: spending by category, over/under budget flags, top 3 actionable cuts
- Key prompt instruction: be specific — name the actual subscriptions or merchants, not generic categories

#### Agent 3 — Savings strategy agent
- Input: income, fixed costs, current savings rate
- Output: recommended savings rate, emergency fund gap, short-term and long-term goal suggestions
- Key prompt instruction: give a concrete dollar amount to save per month, not a percentage

#### Agent 4 — Debt payoff optimizer
- Input: debt profile from Agent 1
- Output: avalanche strategy plan, snowball strategy plan, comparison of total interest paid and months to payoff for each
- Key prompt instruction: show the difference in dollars and months between the two strategies

**Acceptance criteria:**
- All 4 agents return valid JSON within 30 seconds total
- Each agent's output is specific to the uploaded data, not generic
- If a field is missing from the CSV (e.g. no debt accounts), the agent gracefully notes this rather than hallucinating

---

### 6.3 Dashboard

Three panels rendered from agent output:

**Panel 1 — Financial overview**
- Net monthly cash flow (income minus expenses)
- Income vs. spending bar chart (Chart.js)
- Top spending categories

**Panel 2 — Debt breakdown**
- Per-debt progress bars showing balance vs. original estimate
- Payoff timeline (months) for recommended strategy
- Total interest remaining

**Panel 3 — Budget vs. actual**
- Category-level bars comparing spend to a suggested budget
- Over-budget categories highlighted

**AI insight feed**
- Ordered list of the top recommendations across all agents
- Each recommendation is one sentence + one action

**Acceptance criteria:**
- Dashboard renders within 2 seconds of agent responses arriving
- All charts are readable without tooltips
- Empty states display if a category has no data

---

### 6.4 Chat interface

- Text input at bottom of page
- Each message sends: user question + full financial JSON + conversation history → Claude API
- Responses stream into the chat window
- System prompt positions Claude as a financial coach with access to the user's specific data

**Acceptance criteria:**
- Responses reference the user's actual numbers, not generic advice
- Streaming works — text appears token by token
- Chat history persists for the session

---

## 7. Technical architecture

### Stack

| Layer | Choice |
|---|---|
| Frontend | React (Vite) |
| Charts | Chart.js |
| CSV parsing | PapaParse |
| AI | Claude API (`claude-sonnet-4-20250514`) |
| Backend | Node.js / Express (thin API proxy to protect the API key) |
| Storage | In-memory only (no database) |

### Key architectural decision

No vector store or RAG pipeline in this version. The user's parsed financial JSON is injected directly into each agent's system prompt. A typical 1–3 month CSV of transactions is well within Claude's context window. This eliminates the need for embeddings, chunking, and a vector database, saving approximately 2–3 days of setup time.

### Agent call sequence

```
Upload CSV
  → Parse (PapaParse, browser)
  → Build financialJSON
  → Agent 1: Debt analyzer     (Claude API call)
  → Agent 2: Budget coach      (Claude API call)
  → Agent 3: Savings planner   (Claude API call)
  → Agent 4: Payoff optimizer  (Claude API call)
  → Render dashboard
```

Calls are sequential for simplicity. Parallelizing agents 2–4 is a straightforward future optimization.

---

## 8. Day-by-day build plan

### Day 1 — Backend

| Time | Task |
|---|---|
| Morning (~4 hrs) | CSV upload + PapaParse integration, JSON schema normalization, demo data file |
| Afternoon (~4 hrs) | 4 agent system prompts, API call logic, JSON response parsing, error handling |

**End of day 1 checkpoint:** POST a CSV → receive 4 structured JSON responses from all agents.

### Day 2 — Frontend

| Time | Task |
|---|---|
| Morning (~4 hrs) | React app scaffold, file upload UI, dashboard panels, Chart.js charts |
| Afternoon (~4 hrs) | Chat interface with streaming, wire up demo data button, final UI polish, demo walkthrough script |

**End of day 2 checkpoint:** Full working demo with demo data pre-loaded.

---

## 9. Success criteria

The MVP is successful if a demo user can:

1. Upload a CSV (or click "demo data") and see meaningful results in under 60 seconds
2. Read at least 3 specific, actionable recommendations they couldn't get from a generic budgeting app
3. Ask a follow-up question in chat and get a relevant, data-grounded answer
4. Understand the debt payoff comparison (avalanche vs. snowball) without additional explanation

---

## 10. Future scope (post-MVP)

- RAG pipeline for multi-month / multi-document analysis
- User accounts and saved sessions
- What-if scenario engine (slider: "what if I pay $200 extra/month?")
- Proactive alerts for spending anomalies
- Parallel agent invocation for faster load times
- Plaid integration for live bank data
- Mobile layout
