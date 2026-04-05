<div align="center">

# FinanceIQ

### AI-Powered Multi-Agent Financial Advisor

*Upload your bank statement. Get a complete financial health report in under 2 minutes.*

[![Live App](https://img.shields.io/badge/🚀_Live_App-Open_Now-6366f1?style=for-the-badge)](https://ptotic-bernita-unpresciently.ngrok-free.dev/)
&nbsp;
[![Demo](https://img.shields.io/badge/🎥_Demo-Watch_Now-61DAFB?style=for-the-badge&logo=loom&logoColor=white)](https://www.loom.com/share/fb1c5a9d85f7496594eb7f1b34910ad2)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?style=for-the-badge&logo=node.js&logoColor=white)](https://nodejs.org)
[![React](https://img.shields.io/badge/React-18-FF0000?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF6B35?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-50%2B_Models-8B5CF6?style=for-the-badge)](https://openrouter.ai)

---

**[Try our hosted app](https://ptotic-bernita-unpresciently.ngrok-free.dev/)** .
**[Checkout our video demo](https://www.loom.com/share/fb1c5a9d85f7496594eb7f1b34910ad2)** · **[Report Bug](https://github.com/PavithraRajasekar/FinancialAdvisor/issues)** · **[Request Feature](https://github.com/PavithraRajasekar/FinancialAdvisor/issues)**

</div>

---

## What is FinanceIQ?

FinanceIQ ingests any CSV or Excel bank export and runs it through a **6-agent LangGraph pipeline**. Each agent is a specialist that builds on the last. Powered by a multi-agent RAG (Retrieval-Augmented Generation) framework, each stage retrieves relevant financial context, enriches it with domain-specific reasoning, and passes structured insights downstream. The result is a continuously refined, end-to-end financial health analysis delivered in real time, using the AI model of your choice.

<div align="center">

| 📊 Health Score | 💳 Debt Strategy | 🏦 Savings Plan | 📋 Budget | 📧 Email Report |
|:-:|:-:|:-:|:-:|:-:|
| 0–100 score with severity-ranked insights | Avalanche vs Snowball with timeline | Emergency fund + live HY savings rates | Per-category overspend alerts | HTML + PDF via Brevo |

</div>

---

## System Architecture

<div align="center">
  <img src="docImage/financeiq_architecture_v2.svg" alt="FinanceIQ System Architecture" width="100%">
</div>

```mermaid
graph TB
    subgraph CLIENT["🖥️  REACT CLIENT  ·  Vite  ·  Port 5173"]
        direction LR
        Chat["💬 Chat & Upload"]
        Cfg["⚙️ Config Panel\n(keys saved to localStorage)"]
        Dash["📊 Dashboard\n6 interactive tabs"]
        PDF["📄 PDF Export"]
    end

    subgraph SERVER["⚡  EXPRESS SERVER  ·  Node.js  ·  Port 3001"]
        direction LR
        Analyze["POST /api/analyze\n(SSE streaming)"]
        Email["POST /api/send-report\n(PDF + email)"]
        Samples["GET /api/samples"]
    end

    subgraph PYTHON["🐍  PYTHON PIPELINE  ·  LangGraph StateGraph"]
        direction TB
        State(["🗃️ FinancialState\nshared context bus"])

        D1["📂 ① Document Ingestion\nparse · classify · snapshot"]
        D2["🧠 ② Financial Analyzer\nhealth score · insights"]
        D3["💳 ③ Debt Strategist\navalanche / snowball"]
        D4["🏦 ④ Savings Strategist\nemergency fund · goals"]
        D5["📊 ⑤ Budget Advisor\ncategory allocations"]
        D6["📋 ⑥ Report Generator\nmarkdown + charts"]

        State -.-> D1 --> D2 --> D3 --> D4 --> D5 --> D6
    end

    subgraph EXTERNAL["🌐  EXTERNAL SERVICES"]
        LLM["🤖 OpenRouter\n50+ AI Models"]
        Search["🔍 Tavily\nLive Web Search"]
        Brevo["📧 Brevo SMTP\n300 emails/day free"]
    end

    CLIENT <-->|"Server-Sent Events\nreal-time streaming"| SERVER
    SERVER -->|"child_process.spawn"| PYTHON
    PYTHON -->|"LLM API calls"| LLM
    D4 -->|"live savings rates"| Search
    Cfg -->|"creds via request body\n(no .env needed)"| Email
    Email -->|"HTML + PDF\nattachment"| Brevo

    style CLIENT fill:#1e1b4b,stroke:#6366f1,color:#e0e7ff
    style SERVER fill:#052e16,stroke:#22c55e,color:#dcfce7
    style PYTHON fill:#1c1917,stroke:#f97316,color:#fed7aa
    style EXTERNAL fill:#0f172a,stroke:#38bdf8,color:#e0f2fe
```

---

## Agent Pipeline

```mermaid
flowchart LR
    INPUT(["📁 CSV / Excel\nBank Export"])

    subgraph PIPELINE["⚙️  LangGraph StateGraph  ·  FinancialState shared bus"]
        direction LR
        A1["📂 Document\nIngestion"]
        A2["🧠 Financial\nAnalyzer"]
        A3["💳 Debt\nStrategist"]
        A4["🏦 Savings\nStrategist"]
        A5["📊 Budget\nAdvisor"]
        A6["📋 Report\nGenerator"]

        A1 -->|"financial_snapshot"| A2
        A2 -->|"health_score\ninsights"| A3
        A3 -->|"debt_plan"| A4
        A4 -->|"savings_plan"| A5
        A5 -->|"budget_recs"| A6
    end

    LLM[["🤖 OpenRouter\nLLM"]]
    WEB[["🔍 Tavily\nSearch"]]
    OUTPUT(["📊 Dashboard\n+ PDF Report"])

    INPUT --> A1
    A2 & A3 & A4 & A5 & A6 -.->|"LLM call"| LLM
    A4 -.->|"live rates"| WEB
    A6 --> OUTPUT

    style PIPELINE fill:#0f0f23,stroke:#8b5cf6,color:#ddd6fe
    style LLM fill:#1e1b4b,stroke:#6366f1,color:#e0e7ff
    style WEB fill:#082f49,stroke:#0ea5e9,color:#e0f2fe
    style INPUT fill:#064e3b,stroke:#10b981,color:#d1fae5
    style OUTPUT fill:#064e3b,stroke:#10b981,color:#d1fae5
```

---

## Real-Time Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 User
    participant B as 🌐 Browser
    participant E as ⚡ Express
    participant P as 🐍 Pipeline
    participant L as 🤖 OpenRouter
    participant T as 🔍 Tavily

    User->>B: Upload CSV/Excel + goals
    B->>E: POST /api/analyze
    Note over B,E: multipart/form-data

    E->>P: child_process.spawn run_pipeline.py

    P->>L: preflight — validate model (1-token call)
    L-->>P: ✓ model available

    E-->>B: SSE stream open

    loop 6 AI Agents (streamed live)
        P-->>E: {type:"step_start", agent, label}
        E-->>B: SSE → progress bar update
        P->>L: invoke LLM with financial context
        L-->>P: structured JSON response
        P-->>E: {type:"step_done", summary}
        E-->>B: SSE → agent marked complete
    end

    P->>T: search "best high-yield savings accounts"
    T-->>P: live bank rate results

    P-->>E: {type:"done", result: FinancialState}
    E-->>B: SSE stream end

    B->>User: Render full dashboard (6 tabs)
    User->>B: Click "Email Report"
    B->>E: POST /api/send-report + brevoKey
    E->>E: puppeteer → PDF buffer
    E->>User: Email + PDF attachment
```

---

## Tech Stack

<div align="center">

### Frontend
| | Library | Version | Purpose |
|:-:|---------|---------|---------|
| ⚛️ | React | 18.3 | UI framework |
| ⚡ | Vite | 5.3 | Build tool & dev server |
| 🐻 | Zustand | 4.5 | State + localStorage persist |
| 🎭 | Framer Motion | 11 | Animations & transitions |
| 📈 | Recharts | 2.12 | Financial charts |
| 🎨 | Tailwind CSS | 3.4 | Utility-first styling |
| 🎯 | Lucide React | 0.408 | Icon system |

### Backend
| | Package | Purpose |
|:-:|---------|---------|
| 🚂 | Express 4 | HTTP server & SSE routing |
| 📁 | Multer | Multipart file upload |
| 📧 | Nodemailer | SMTP email delivery |
| 📄 | puppeteer-core | HTML → PDF (uses system Chrome) |

### AI Engine (Python)
| | Library | Version | Purpose |
|:-:|---------|---------|---------|
| 🕸️ | LangGraph | 1.1 | Multi-agent StateGraph |
| 🔗 | LangChain | 1.2 | LLM abstraction layer |
| 🤖 | langchain-openai | 1.1 | OpenRouter connector |
| 🌐 | OpenRouter | — | 50+ model gateway |
| 🔍 | Tavily | 0.3 | Real-time web search |
| 🐼 | pandas | 3.0 | CSV/Excel parsing |

</div>

---

## Getting Started

### ⚡ Option 1 — Use the Hosted App (No Setup)

**[https://ptotic-bernita-unpresciently.ngrok-free.dev/](https://ptotic-bernita-unpresciently.ngrok-free.dev/)**

1. Open the link above
2. Go to **Config** → paste your [OpenRouter API key](https://openrouter.ai/keys) (free)
3. Upload any CSV/Excel bank export and click **Analyze**

---

### 💻 Option 2 — Run Locally

#### Manual setup

```bash
# 1 · Python environment
python3 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2 · Node dependencies
cd server && npm install && cd ..
cd client && npm install && cd ..

# 3a · Start API server (Terminal 1)
cd server && node server.js

# 3b · Start React dev server (Terminal 2)
cd client && npm run dev

# 4 . Start exploring in the browser
Open **[http://localhost:5173](http://localhost:5173)**
```

---

## Configuration

All credentials are entered in-app and stored in your browser — nothing is sent to our servers at rest.

<div align="center">

| Setting | Where in App | Required | Get it free |
|---------|-------------|:--------:|-------------|
| OpenRouter API Key | Config → API Keys | ✅ | [openrouter.ai/keys](https://openrouter.ai/keys) |
| Tavily API Key | Config → API Keys | Optional | [app.tavily.com](https://app.tavily.com) |
| Brevo SMTP Key | Config → Email Settings | Optional | [app.brevo.com](https://app.brevo.com) |
| From Email Address | Config → Email Settings | Optional | Your Brevo account email |

</div>

### AI Models

FinanceIQ supports 13 models across OpenAI, Anthropic, Google, Meta, Mistral, DeepSeek, and StepFun — switchable in Config with no restart needed.

<div align="center">

| Tier | Model | Best for |
|------|-------|---------|
| 🏆 Recommended | GPT-4o Mini | Most users — fast, reliable, great JSON |
| 💡 Best accuracy | Claude 3.5 Sonnet | Polished report writing |
| 💰 Best value | DeepSeek V3 (paid) | GPT-4 quality at low cost |
| 🆓 Best free | Llama 3.3 70B | Maximum capability at zero cost |
| ⚡ Fastest free | Step 3.5 Flash | Quick analyses |

</div>

> **Note on free models:** Free OpenRouter endpoints have rate limits and can occasionally be unavailable. Switch to a paid model if you see a "no active endpoints" error.

---

## Email Reports

Email delivery is configured entirely in-app — no `.env` file needed.

```
1. Sign up at app.brevo.com (free, no credit card, 300 emails/day)
2. Go to: SMTP & API → SMTP tab → Generate SMTP Key
3. In FinanceIQ: Config → Email Settings
   ┌─────────────────────────────────────────────────┐
   │  Brevo SMTP Key    │  xsmtpsib-...               │
   │  From Email        │  you@yourdomain.com          │
   └─────────────────────────────────────────────────┘
4. Dashboard → Report tab → Send Report Email
```

Each email includes a styled HTML report + an **A4 PDF attachment** rendered by headless Chrome.

---

## Project Structure

```
group_19/
│
├── 📋 requirements.txt      Python dependencies
├── 🔧 .env.example          Env template (OpenRouter + Tavily only)
│
├── agents/                  Python LangGraph agents
│   ├── state.py             FinancialState TypedDict — shared bus
│   ├── orchestrator.py      StateGraph definition + SSE streaming
│   ├── document_ingestion.py  Agent 1 · parse & classify transactions
│   ├── financial_analyzer.py  Agent 2 · health score + insights
│   ├── debt_strategist.py     Agent 3 · debt payoff strategy
│   ├── savings_strategy.py    Agent 4 · savings goals + bank rates
│   ├── budget_advisor.py      Agent 5 · category budgets + alerts
│   ├── report_generator.py    Agent 6 · final report + charts
│   └── run_pipeline.py        Entry · model validation + pipeline runner
│
├── utils/
│   ├── llm_config.py        get_llm() · validate_model() · parse_llm_json()
│   └── file_parser.py       CSV/Excel ingestion + column normalisation
│
├── data/sample_data/        Sample transaction files for demo
│
├── server/
│   └── server.js            Express · SSE · PDF generation · Brevo email
│
└── client/src/
    ├── store/financialStore.js    Zustand state + localStorage + migrations
    ├── pages/
    │   ├── ChatPage.jsx           Conversational upload + live progress
    │   ├── ConfigPage.jsx         API keys · model · email settings
    │   ├── DashboardPage.jsx      6-tab results dashboard
    │   └── DocsPage.jsx           Interactive architecture docs
    └── components/dashboard/
        ├── OverviewTab.jsx        Health score + ring charts
        ├── InsightsTab.jsx        Severity-ranked AI insights
        ├── BudgetTab.jsx          Category budget allocations
        ├── DebtTab.jsx            Payoff strategy + timeline
        ├── SavingsTab.jsx         Emergency fund + live rates
        └── ReportTab.jsx          Markdown report + PDF + email
```

---

## Troubleshooting

<details>
<summary><b>❌ "Model has no active endpoints" error</b></summary>

The selected free model's endpoint is temporarily unavailable or has been removed from OpenRouter.

**Fix:** Go to **Config → AI Model** and switch to:
- **GPT-4o Mini** (paid, most reliable)
- **Llama 3.3 70B** (free, most stable)

Free models rotate on/off OpenRouter — paid models are always available.
</details>

<details>
<summary><b>❌ "Chrome/Chromium not found" — PDF won't generate</b></summary>

puppeteer-core needs a local Chrome/Chromium installation.

**macOS:** Install [Google Chrome](https://www.google.com/chrome/) to `/Applications/`

**Linux:**
```bash
sudo apt-get install chromium-browser   # Debian/Ubuntu
```

The HTML report will still download and the email will still send — just without the PDF attachment.
</details>

<details>
<summary><b>❌ Email not sending</b></summary>

1. Open **Config → Email Settings**
2. Verify your **Brevo SMTP Key** starts with `xsmtpsib-`
3. Verify **From Email** matches the sender address in your Brevo account
4. Check [app.brevo.com](https://app.brevo.com) → SMTP & API → SMTP tab for key rotation

> Note: Brevo's `xkeysib-` keys are REST API keys and will NOT work for SMTP.
</details>

<details>
<summary><b>❌ Python agents not starting</b></summary>

```bash
# Ensure virtual environment is active
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# Re-install dependencies
pip install -r requirements.txt

# Verify Python version
python3 --version   # must be 3.11+
```
</details>

<details>
<summary><b>❌ Port 3001 already in use</b></summary>

```bash
# macOS / Linux
lsof -ti:3001 | xargs kill -9

# Windows
netstat -ano | findstr :3001
taskkill /PID <PID> /F
```
</details>

---

<div align="center">

Built with ❤️ using LangGraph, React, and OpenRouter

[![Live App](https://img.shields.io/badge/🚀_Try_It_Now-Live_App-6366f1?style=for-the-badge)](https://ptotic-bernita-unpresciently.ngrok-free.dev/)

</div>
