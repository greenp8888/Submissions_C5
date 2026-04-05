# 💰 AI Financial Coach

**Agentic, RAG-powered, MCP-enabled Financial Intelligence Platform**

---

## 🚀 Overview

AI Financial Coach is an end-to-end intelligent financial analysis system that transforms raw bank statements into actionable insights using:

- 🧠 **Agentic AI workflows**
- 🔎 **RAG (Retrieval-Augmented Generation)**
- 🔗 **MCP (Model Context Protocol) tool orchestration**
- 📊 **Real-time analytics & visualizations**
- 💡 **Cost-aware LLM execution with observability**
- 📧 **Automation via n8n workflows**

Unlike traditional dashboards, this system **reasons, explains, and acts** using structured financial intelligence.

---

## 🖥️ Product Experience

The application provides a modern financial intelligence dashboard inspired by enterprise tools:

- 📊 **Zeni-style split layout** (input + insights side-by-side)
- 💰 KPI cards (credits, expenses, savings, financial health)
- 📈 Interactive visual analytics (trends, category mix, comparisons)
- 🧠 AI insights panel with reasoning outputs
- ⚙️ Runtime observability panel (MCP + tokens + traces)
- 📧 Email automation via n8n

Designed to resemble real-world SaaS financial platforms.

---

## 🎯 Key Capabilities

### 📥 Data Ingestion

- Upload structured financial data:
  - CSV
  - Excel (.xlsx)
- Automatic validation and normalization

---

### 🤖 Agentic AI Architecture

The system follows an **Agentic AI design pattern**:

- Each financial function is handled by a **specialized agent**
- Agents operate in a **coordinated pipeline**
- MCP enables **external tool execution**
- RAG provides **contextual memory**
- LLM acts as the **reasoning engine**

This makes the system modular, explainable, and extensible.

---

### 🧠 Multi-Agent Financial Analysis

| Agent              | Function                             |
|------------------|------------------------------------|
| Document Reader    | Parses and standardizes transactions |
| Expense Classifier | Categorizes spending               |
| Debt Analyzer      | Computes debt pressure             |
| Savings Strategist | Calculates surplus & savings plan  |
| Recurring Detector | Identifies repeat expenses         |
| Anomaly Detector   | Flags unusual transactions         |
| Merchant Analyzer  | Ranks merchants by spend           |
| Report Builder     | Generates final financial summary  |

---

### 🔎 Smart Search (RAG)

- FAISS-based vector search
- Context retrieval from transactions
- Evidence-backed responses with citations like `[R1], [R2]`

---

### 🔗 MCP Integration (Real Tool Execution)

- External MCP server (`mcp_server.py`)
- Executes real financial tools:
  - `summarize_transactions`
  - `analyze_debt_pressure`
  - `savings_plan`

- Provides runtime proof:
  - tool calls
  - execution logs
  - structured outputs

---

### 🧠 LLM Integration (OpenRouter / HuggingFace)

- Structured LLM responses:
  - `text`
  - `usage`
  - `status`
  - `raw payload`

- Supports models:
  - Gemini Flash
  - LLaMA
  - Mistral
  - Qwen

---

### 💰 Token Usage Observability

- Displays **real provider token usage**:
  - prompt tokens
  - completion tokens
  - total tokens

- Falls back to estimation if provider data unavailable

---

### 📡 LangSmith Observability

- Full traceability of LLM workflows
- Run IDs and execution stages
- Debug and monitoring support

---

### ⚙️ Runtime Observability

The system provides full transparency into execution:

- MCP execution logs and tool calls
- Token usage (real vs estimated)
- LangSmith trace metadata
- Error tracking and fallback logs

---

### 📊 Visual Analytics

- Category distribution (Pie chart)
- Spending trends (Line chart)
- Monthly breakdown (Bar chart)
- Credit vs Debit comparison

---

### 📧 Automation (n8n Integration)

After analysis, users can trigger an email workflow via n8n:

- Sends summarized financial insights
- Uses webhook-based orchestration
- Demonstrates real-world automation capability

---

## 🔄 End-to-End Flow

1. User uploads financial data
2. Data is validated and normalized
3. Multi-agent pipeline processes insights
4. MCP executes external financial tools
5. RAG retrieves supporting evidence
6. LLM generates reasoning-based responses
7. Results are visualized in dashboard
8. Optional automation sends report via email

---

## 🏗️ Architecture

```text
                ┌──────────────────────────┐
                │   User Upload (CSV/XLSX) │
                └────────────┬─────────────┘
                             │
                     Data Processing
                             │
                ┌────────────▼────────────┐
                │ Multi-Agent Pipeline     │
                │ (Classification, Debt,   │
                │ Savings, Anomaly, etc.)  │
                └────────────┬────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
   RAG (FAISS)        MCP Server         LLM (OpenRouter)
 Context Retrieval   Tool Execution     Reasoning Engine
         │                   │                   │
         └────────────┬──────┴──────┬────────────┘
                      ▼             ▼
               Final Insights + Dashboard