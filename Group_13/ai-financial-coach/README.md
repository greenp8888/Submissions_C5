<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# AI Financial Coach

This project is an AI-powered financial coach with:
- structured financial data storage in SQLite
- server-side RAG retrieval
- an orchestrator agent
- specialist agents for debt, savings, budget, portfolio, tax, goals, coaching, and document parsing

## 1. Set Up The Code

**Prerequisites**
- Node.js 18+
- npm

**Install and run**
1. Clone the repository.
2. Move into the project folder.
3. Install dependencies:
   `npm install`
4. Create a `.env` file in the project root.
5. Add your OpenRouter API key to the `.env` file.
6. Start the app:
   `npm run dev`
7. Open:
   [http://localhost:3000](http://localhost:3000)

## 2. Add The OpenRouter API Key

Create a `.env` file in the root of the project and add:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
APP_URL=http://localhost:3000
JWT_SECRET=your_secret_here
```

Notes:
- `OPENROUTER_API_KEY` is required for all LLM agent responses.
- `APP_URL` is used in OpenRouter request headers.
- `JWT_SECRET` is used for local authentication.

## 3. Sample Queries To Test In The UI

Use these in the chat UI after adding some financial data:

### Debt Analyzer
- `Analyze my debt and suggest avalanche vs snowball payoff`
- `What exact loan should I close first?`
- `How risky is my current EMI burden?`

Expected output:
- DTI ratio
- active loans
- recommended payoff strategy
- next action items

### Savings Strategist
- `Build a savings plan for my emergency fund and goals`
- `How much can I invest every month safely?`
- `What SIP plan should I follow for my goals?`

Expected output:
- monthly surplus
- emergency fund target and gap
- goal-wise SIP plan
- warnings if surplus is insufficient

### Budget Advisor
- `Show where I can reduce my monthly expenses`
- `Am I overspending anywhere?`
- `Which categories should I cut first?`

Expected output:
- total spend vs budget
- category breakdown
- reduction suggestions
- potential savings

### Portfolio Agent
- `Rebalance my portfolio based on my current holdings`
- `What exact portfolio actions should I take now?`
- `How is my current asset allocation looking?`

Expected output:
- current allocation
- target allocation
- exact buy/sell actions
- stress-test view

### Tax Agent
- `Find tax-saving opportunities under 80C and 80D`
- `How much 80C gap do I still have?`
- `What tax-saving instruments should I consider?`

Expected output:
- 80C used and remaining gap
- potential additional tax savings
- recommended instruments

### Goal Planning Agent
- `Am I on track for my goals?`
- `Which goal is at risk?`
- `What happens if I save 5000 more every month?`

Expected output:
- goal progress
- health score summary
- at-risk goals
- what-if scenario

### Coach Narrator
- `Explain my financial health score simply`
- `Summarize my current financial health`

Expected output:
- plain-language summary
- strengths
- priority actions

### Document Parser
- `Parse this document and summarize it`
- `Extract the details from this bank statement`
- `Summarize this uploaded financial document`

Expected output:
- document type
- key summary figures
- extracted table count
- parsing notes

To test document parsing from chat:
1. Click the attachment icon in the chat box.
2. Upload a PDF, CSV, Excel file, or image.
3. Send one of the document parsing queries above.

## RAG Chat Pipeline

The chat flow now runs as a server-side RAG pipeline:

1. User sends a query from the dashboard chat UI
2. The server reads the authenticated user's financial records from `finance.db`
3. Those records are converted into structured RAG documents
4. Documents are indexed into a SQLite-backed local vector store (`RagDocuments` table in `finance.db`)
5. The query retrieves the most relevant documents with hashed-vector similarity plus keyword overlap
6. Retrieved context is passed into the LangGraph orchestrator
7. The orchestrator routes the request to the right specialist agent
8. The specialist agent answers using retrieved financial context as the source of truth

### Vector database used

This project uses a local SQLite-backed vector store inside `finance.db` via `better-sqlite3`.
The vector index is stored in the `RagDocuments` table and uses hashed embedding vectors generated in-app.

## Supported Agent Flows

- Debt Analyzer
- Savings Strategist
- Budget Advisor
- Portfolio Agent
- Tax Agent
- Goal Planning Agent
- Coach Narrator
- Financial Literacy Agent
- Document Parser Agent

## Notes

- The vector database used in this project is a SQLite-backed local vector store inside `finance.db`.
- The chat UI now supports direct document upload for parser queries.
