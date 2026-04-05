import { useState } from "react";
import { motion } from "framer-motion";
import {
  Server, Globe, Brain, Search, Database, ArrowRight,
  Zap, FileText, BarChart2, Shield, ChevronDown, ChevronRight,
  MessageSquare, Upload, PlayCircle, CheckCircle2,
} from "lucide-react";

// ── Reusable card ─────────────────────────────────────────────────────────────
function Card({ children, className = "", style = {} }) {
  return (
    <div
      className={`glass rounded-2xl p-5 ${className}`}
      style={style}
    >
      {children}
    </div>
  );
}

// ── Section heading ───────────────────────────────────────────────────────────
function SectionTitle({ icon: Icon, label, color = "#8B5CF6" }) {
  return (
    <div className="flex items-center gap-2.5 mb-4">
      <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
        style={{ background: `${color}18`, border: `1px solid ${color}35` }}>
        <Icon size={14} style={{ color }} />
      </div>
      <h2 className="text-white font-bold text-sm tracking-tight">{label}</h2>
    </div>
  );
}

// ── Agent Pipeline node ───────────────────────────────────────────────────────
const AGENTS = [
  {
    id: "document_ingestion",
    icon: "📂",
    name: "Document Ingestion",
    tagline: "Parse & classify",
    color: "#06B6D4",
    desc: "Reads CSV/Excel, normalises columns, classifies every row as Income / Expense / Transfer / Refund, and builds the financial snapshot.",
    outputs: ["financial_snapshot", "expense_by_category", "income_sources"],
  },
  {
    id: "financial_analyzer",
    icon: "🧠",
    name: "Financial Analyzer",
    tagline: "Score & insight",
    color: "#8B5CF6",
    desc: "Computes the 0–100 Financial Health Score using a weighted formula across 5 dimensions, then generates 4–8 personalised insights ordered by severity.",
    outputs: ["health_score", "financial_insights"],
  },
  {
    id: "debt_strategist",
    icon: "💳",
    name: "Debt Strategist",
    tagline: "Payoff strategy",
    color: "#EF4444",
    desc: "Detects debt signals (loan repayments, credit card fees) and recommends either Avalanche (highest APR first) or Snowball (smallest balance first).",
    outputs: ["debt_plan", "action_steps", "timeline_months"],
  },
  {
    id: "savings_strategy",
    icon: "🏦",
    name: "Savings Strategist",
    tagline: "Emergency & goals",
    color: "#10B981",
    desc: "Targets a 3–6 month emergency fund, sets personalised savings goals from user intent, and queries Tavily for live high-yield savings account rates.",
    outputs: ["savings_plan", "emergency_fund", "bank_offers"],
  },
  {
    id: "budget_advisor",
    icon: "📊",
    name: "Budget Advisor",
    tagline: "Allocation & alerts",
    color: "#F59E0B",
    desc: "Analyses spend per category, flags overages with percentage variance, and recommends 5–15% reductions to free up cash each month.",
    outputs: ["budget_recommendations", "allocations", "alerts"],
  },
  {
    id: "report_generator",
    icon: "📋",
    name: "Report Generator",
    tagline: "Synthesise & present",
    color: "#EC4899",
    desc: "Consolidates all agent outputs into a Markdown financial report and builds chart data for the dashboard visualisations.",
    outputs: ["final_report", "charts"],
  },
];

function AgentNode({ agent, index, expanded, onToggle }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06 }}
      className="flex flex-col"
    >
      <div
        onClick={onToggle}
        className="flex items-center gap-3 p-4 rounded-xl cursor-pointer transition-all duration-200"
        style={{
          background: expanded ? `${agent.color}0f` : "rgba(255,255,255,0.025)",
          border: `1px solid ${expanded ? agent.color + "30" : "rgba(255,255,255,0.07)"}`,
        }}
      >
        {/* Step number */}
        <div className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0"
          style={{ background: agent.color + "20", color: agent.color, border: `1px solid ${agent.color}35` }}>
          {index + 1}
        </div>
        <span className="text-xl flex-shrink-0">{agent.icon}</span>
        <div className="flex-1 min-w-0">
          <p className="text-white text-sm font-semibold leading-none">{agent.name}</p>
          <p className="text-[11px] mt-0.5" style={{ color: agent.color }}>{agent.tagline}</p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <div className="hidden sm:flex flex-wrap gap-1">
            {agent.outputs.slice(0, 2).map(o => (
              <span key={o} className="text-[9px] px-1.5 py-0.5 rounded font-mono"
                style={{ background: agent.color + "12", color: agent.color + "cc", border: `1px solid ${agent.color}18` }}>
                {o}
              </span>
            ))}
          </div>
          {expanded ? <ChevronDown size={13} className="text-slate-500" /> : <ChevronRight size={13} className="text-slate-500" />}
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="overflow-hidden"
        >
          <div className="mx-4 mb-2 p-4 rounded-xl text-xs text-slate-300 leading-relaxed"
            style={{ background: "rgba(255,255,255,0.02)", borderLeft: `2px solid ${agent.color}50` }}>
            <p className="mb-3">{agent.desc}</p>
            <div className="flex flex-wrap gap-1.5">
              <span className="text-slate-500 text-[10px] font-medium mr-1">Emits →</span>
              {agent.outputs.map(o => (
                <span key={o} className="text-[10px] px-2 py-0.5 rounded-full font-mono"
                  style={{ background: agent.color + "15", color: agent.color, border: `1px solid ${agent.color}28` }}>
                  {o}
                </span>
              ))}
            </div>
          </div>
        </motion.div>
      )}

      {/* Arrow connector (not on last) */}
      {index < AGENTS.length - 1 && (
        <div className="flex justify-start pl-[22px] my-0.5">
          <div className="flex flex-col items-center gap-0.5">
            <div className="w-px h-2 bg-white/[0.07]" />
            <ArrowRight size={11} className="text-slate-700 rotate-90" />
          </div>
        </div>
      )}
    </motion.div>
  );
}

// ── Tech stack cards ──────────────────────────────────────────────────────────
const STACK = [
  {
    layer: "Frontend",
    icon: Globe,
    color: "#06B6D4",
    items: [
      { name: "React 18", note: "UI framework" },
      { name: "Vite 5", note: "Build & dev server" },
      { name: "Zustand + persist", note: "State + localStorage" },
      { name: "Framer Motion", note: "Animations" },
      { name: "Recharts", note: "Financial charts" },
      { name: "Tailwind CSS", note: "Utility styles" },
    ],
  },
  {
    layer: "Backend",
    icon: Server,
    color: "#8B5CF6",
    items: [
      { name: "Node.js + Express", note: "API server (port 3001)" },
      { name: "Multer", note: "File upload handling" },
      { name: "SSE (Server-Sent Events)", note: "Real-time streaming" },
      { name: "child_process.spawn", note: "Python bridge" },
      { name: "Nodemailer", note: "Email report delivery" },
      { name: "dotenv", note: "Environment config" },
    ],
  },
  {
    layer: "AI Engine",
    icon: Brain,
    color: "#8B5CF6",
    items: [
      { name: "LangGraph", note: "Multi-agent orchestration" },
      { name: "LangChain OpenAI", note: "LLM interface" },
      { name: "OpenRouter", note: "Multi-model API gateway" },
      { name: "Python 3.11+", note: "Agent runtime" },
      { name: "openpyxl / pandas", note: "File parsing" },
    ],
  },
  {
    layer: "Search & Data",
    icon: Search,
    color: "#10B981",
    items: [
      { name: "Tavily API", note: "Live web research" },
      { name: "Bank rate search", note: "Savings account offers" },
      { name: "Market data", note: "Regional finance info" },
    ],
  },
];

// ── Data flow steps ───────────────────────────────────────────────────────────
const FLOW_STEPS = [
  { icon: Upload,         label: "Upload",    detail: "User selects CSV or Excel file",                       color: "#06B6D4" },
  { icon: MessageSquare,  label: "Chat",      detail: "Goals collected, config confirmed",                    color: "#8B5CF6" },
  { icon: Server,         label: "Express",   detail: "POST /api/analyze — file + config",                   color: "#F59E0B" },
  { icon: PlayCircle,     label: "Python",    detail: "run_pipeline.py spawned as child process",             color: "#EC4899" },
  { icon: Brain,          label: "LangGraph", detail: "6-node StateGraph runs sequentially",                  color: "#8B5CF6" },
  { icon: Search,         label: "Tavily",    detail: "Live savings rates fetched (savings agent)",           color: "#10B981" },
  { icon: Zap,            label: "SSE",       detail: "Step events streamed to client in real-time",          color: "#F59E0B" },
  { icon: BarChart2,      label: "Dashboard", detail: "Result rendered across 6 interactive tabs",            color: "#06B6D4" },
];

// ── Models table ──────────────────────────────────────────────────────────────
const MODELS = [
  { name: "GPT-4o Mini",              provider: "OpenAI",    speed: 95, accuracy: 78, cost: "~$0.0002/1k", tag: "Default",      emoji: "⚡" },
  { name: "GPT-4o",                   provider: "OpenAI",    speed: 70, accuracy: 95, cost: "~$0.005/1k",  tag: "Best accuracy",emoji: "🧠" },
  { name: "GPT-4 Turbo",              provider: "OpenAI",    speed: 80, accuracy: 92, cost: "~$0.01/1k",   tag: "Powerful",     emoji: "🚀" },
  { name: "Claude 3.5 Sonnet",        provider: "Anthropic", speed: 75, accuracy: 93, cost: "~$0.003/1k",  tag: "Best reports", emoji: "🎯" },
  { name: "Claude 3 Haiku",           provider: "Anthropic", speed: 92, accuracy: 76, cost: "~$0.0003/1k", tag: "Fast Claude",  emoji: "💨" },
  { name: "Gemini Flash 1.5",         provider: "Google",    speed: 93, accuracy: 74, cost: "Free tier",   tag: "Free",         emoji: "✨" },
  { name: "Gemini Pro 1.5",           provider: "Google",    speed: 78, accuracy: 85, cost: "~$0.001/1k",  tag: "Balanced",     emoji: "🌟" },
  { name: "Llama 3.1 8B",             provider: "Meta",      speed: 85, accuracy: 65, cost: "Free",        tag: "Open source",  emoji: "🦙" },
  { name: "Mistral Nemo",             provider: "Mistral",   speed: 88, accuracy: 72, cost: "Free",        tag: "Free",         emoji: "🌬️" },
];

function MiniBar({ value, color }) {
  return (
    <div className="flex items-center gap-1">
      <div className="w-16 h-1 rounded-full overflow-hidden bg-white/[0.06]">
        <div className="h-full rounded-full" style={{ width: `${value}%`, background: color }} />
      </div>
      <span className="text-[10px] text-slate-500 font-mono w-5">{value}</span>
    </div>
  );
}

// ── MCP / Tools / Protocols section ──────────────────────────────────────────
const MCP_ITEMS = [
  {
    title: "LangGraph StateGraph — Agent Context Protocol",
    icon: Database,
    color: "#8B5CF6",
    body: "Every agent reads from and writes to a single FinancialState TypedDict — the inter-agent context bus. No direct agent-to-agent calls; each agent receives the full accumulated state and returns only its own output keys. This mirrors the Model Context Protocol (MCP) pattern: structured context passed between autonomous reasoning units.",
    tags: ["LangGraph", "StateGraph", "TypedDict", "Sequential DAG"],
  },
  {
    title: "Tavily — Live Web Search Tool",
    icon: Search,
    color: "#10B981",
    body: "The Savings Strategist invokes Tavily as an external tool call. It formulates a search query (\"best high-yield savings accounts\"), retrieves live results with URL + snippet, and injects structured bank_offers into the savings plan. Tavily is the only live-data tool in the pipeline.",
    tags: ["TavilySearchResults", "Tool calling", "Live bank rates", "Web RAG"],
  },
  {
    title: "OpenRouter — Unified Model Gateway",
    icon: Brain,
    color: "#06B6D4",
    body: "All LLM calls route through OpenRouter's unified API (base_url: openrouter.ai/api/v1) using LangChain's ChatOpenAI connector. This decouples every agent from any single provider — swap GPT-4o for Claude or Gemini in Config without touching agent code. The gateway also handles token counting, rate limits, and fallbacks.",
    tags: ["ChatOpenAI", "LangChain", "Multi-provider", "OpenRouter API v1"],
  },
  {
    title: "SSE — Real-time Agent Streaming Protocol",
    icon: Zap,
    color: "#F59E0B",
    body: "Python stdout → Node.js child_process.spawn → Express SSE response. Each agent emits step_start / step_done / done as JSON lines on stdout. Express forwards them as Server-Sent Events. The React client reads with the Fetch Streams API (getReader) and updates the progress UI in real-time — no WebSocket needed.",
    tags: ["Server-Sent Events", "child_process.spawn", "Streams API", "JSON-lines"],
  },
  {
    title: "File Parsing — Multi-format Ingestion Tool",
    icon: FileText,
    color: "#EC4899",
    body: "The Document Ingestion agent uses openpyxl (Excel) and pandas (CSV) to parse uploaded files. It normalises column names via fuzzy matching (date/amount/category/type), classifies each row as Income / Expense / Transfer / Refund using rule-based logic, and builds the financial_snapshot dict passed to all downstream agents.",
    tags: ["openpyxl", "pandas", "Column normalisation", "Transaction classification"],
  },
  {
    title: "LangChain JSON Parsing — Structured Output",
    icon: Database,
    color: "#F97316",
    body: "Every agent uses a structured output contract: the system prompt specifies an exact JSON schema, and responses are parsed by parse_llm_json() — a robust utility that strips markdown fences, extracts the outermost JSON object via brace matching, removes JS-style trailing commas and comments, and falls back gracefully. On failure, errors are appended to the shared errors list without crashing the pipeline.",
    tags: ["Structured output", "JSON schema prompting", "parse_llm_json", "Robust parsing", "Error accumulation"],
  },
  {
    title: "Nodemailer — Email Report Delivery",
    icon: MessageSquare,
    color: "#06B6D4",
    body: "The POST /api/send-report endpoint accepts a recipient email, subject, and HTML body. It reads up to 5 SMTP provider configurations from environment variables (EMAIL_1_HOST/USER/PASS through EMAIL_5_*) and rotates between them round-robin to avoid exhausting any single provider's free-tier limit. Supports any SMTP service (Gmail App Password, Brevo, SendGrid, Mailgun) as well as nodemailer service shorthands. The React client builds a branded HTML summary email with health score, key metrics, and top insights before posting to this endpoint.",
    tags: ["Nodemailer", "SMTP rotation", "Round-robin", "Free tier", "HTML email", "Multi-provider"],
  },
];

// ── Architecture diagram ──────────────────────────────────────────────────────
function ArchDiagram() {
  return (
    <div className="w-full overflow-x-auto">
      <div className="min-w-[560px]">
        {/* Top row: 3 main layers */}
        <div className="flex items-stretch gap-3 mb-3">
          {/* React Client */}
          <div className="flex-1 rounded-xl p-3 flex flex-col gap-2"
            style={{ background: "rgba(6,182,212,0.08)", border: "1px solid rgba(6,182,212,0.25)" }}>
            <div className="flex items-center gap-2">
              <Globe size={12} className="text-cyan-400 flex-shrink-0" />
              <span className="text-cyan-400 text-[11px] font-bold">React Client</span>
              <span className="ml-auto text-[9px] text-slate-600 font-mono">:5173</span>
            </div>
            {["Chat UI", "Config Panel", "Dashboard (6 tabs)", "PDF Export", "Email Modal"].map(t => (
              <div key={t} className="text-[10px] text-slate-400 pl-1 flex items-center gap-1.5">
                <span className="w-1 h-1 rounded-full bg-cyan-400/50 flex-shrink-0" />
                {t}
              </div>
            ))}
          </div>

          {/* Arrow */}
          <div className="flex items-center flex-shrink-0">
            <div className="flex flex-col items-center gap-0.5">
              <ArrowRight size={12} className="text-slate-600" />
              <div className="w-px h-3 bg-slate-700" />
              <ArrowRight size={12} className="text-slate-600 rotate-180" />
            </div>
          </div>

          {/* Express Server */}
          <div className="flex-1 rounded-xl p-3 flex flex-col gap-2"
            style={{ background: "rgba(139,92,246,0.08)", border: "1px solid rgba(139,92,246,0.25)" }}>
            <div className="flex items-center gap-2">
              <Server size={12} className="text-purple-400 flex-shrink-0" />
              <span className="text-purple-400 text-[11px] font-bold">Express Server</span>
              <span className="ml-auto text-[9px] text-slate-600 font-mono">:3001</span>
            </div>
            {["POST /api/analyze", "POST /api/send-report", "GET /api/samples", "Multer file upload", "SSE streaming"].map(t => (
              <div key={t} className="text-[10px] text-slate-400 pl-1 flex items-center gap-1.5">
                <span className="w-1 h-1 rounded-full bg-purple-400/50 flex-shrink-0" />
                {t}
              </div>
            ))}
          </div>

          {/* Arrow */}
          <div className="flex items-center flex-shrink-0">
            <div className="flex flex-col items-center gap-0.5">
              <ArrowRight size={12} className="text-slate-600" />
              <div className="w-px h-3 bg-slate-700" />
              <span className="text-[8px] text-slate-600 font-mono whitespace-nowrap">spawn</span>
            </div>
          </div>

          {/* Python Pipeline */}
          <div className="flex-1 rounded-xl p-3 flex flex-col gap-2"
            style={{ background: "rgba(236,72,153,0.08)", border: "1px solid rgba(236,72,153,0.25)" }}>
            <div className="flex items-center gap-2">
              <Brain size={12} className="text-pink-400 flex-shrink-0" />
              <span className="text-pink-400 text-[11px] font-bold">Python / LangGraph</span>
            </div>
            {["run_pipeline.py", "StateGraph (6 nodes)", "JSON-lines stdout", "FinancialState bus", "parse_llm_json()"].map(t => (
              <div key={t} className="text-[10px] text-slate-400 pl-1 flex items-center gap-1.5">
                <span className="w-1 h-1 rounded-full bg-pink-400/50 flex-shrink-0" />
                {t}
              </div>
            ))}
          </div>
        </div>

        {/* Middle connector line */}
        <div className="flex justify-end pr-[33%] pl-[67%] mb-3">
          <div className="w-px h-4 bg-white/[0.06] mx-auto" />
        </div>

        {/* Bottom row: External APIs */}
        <div className="flex gap-3">
          <div className="flex-1 rounded-xl p-3 flex flex-col gap-2"
            style={{ background: "rgba(16,185,129,0.07)", border: "1px solid rgba(16,185,129,0.2)" }}>
            <div className="flex items-center gap-2">
              <Search size={12} className="text-emerald-400 flex-shrink-0" />
              <span className="text-emerald-400 text-[11px] font-bold">External APIs</span>
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 mt-1">
              {[
                { name: "OpenRouter", note: "LLM gateway (50+ models)", color: "#8B5CF6" },
                { name: "Tavily", note: "Live web search", color: "#10B981" },
                { name: "Brevo SMTP", note: "Email + PDF attachment", color: "#06B6D4" },
                { name: "puppeteer-core", note: "HTML→PDF (local Chrome)", color: "#F59E0B" },
              ].map(({ name, note, color }) => (
                <div key={name} className="flex items-start gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full flex-shrink-0 mt-1" style={{ background: color }} />
                  <div>
                    <span className="text-[10px] text-white font-medium">{name}</span>
                    <span className="text-[9px] text-slate-500 ml-1">{note}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Agent pipeline visual diagram ─────────────────────────────────────────────
function PipelineDiagram() {
  const steps = [
    { icon: "📂", name: "Document Ingestion",  color: "#06B6D4", out: "financial_snapshot" },
    { icon: "🧠", name: "Financial Analyzer",  color: "#8B5CF6", out: "health_score · insights" },
    { icon: "💳", name: "Debt Strategist",      color: "#EF4444", out: "debt_plan" },
    { icon: "🏦", name: "Savings Strategist",   color: "#10B981", out: "savings_plan", ext: "Tavily" },
    { icon: "📊", name: "Budget Advisor",       color: "#F59E0B", out: "budget_recommendations" },
    { icon: "📋", name: "Report Generator",     color: "#EC4899", out: "final_report · charts" },
  ];

  return (
    <div className="flex flex-col">
      {/* State bus banner */}
      <div className="mb-4 px-3 py-2 rounded-xl text-center text-[10px] font-mono text-slate-400"
        style={{ background: "rgba(255,255,255,0.02)", border: "1px dashed rgba(255,255,255,0.08)" }}>
        <span className="text-slate-500">FinancialState</span>
        {" · "}
        {["raw_data","financial_snapshot","health_score","financial_insights","debt_plan","savings_plan","budget_recommendations","final_report","charts","errors"]
          .map((k, i) => <span key={k}>{i > 0 && " · "}<span style={{ color: "rgba(139,92,246,0.8)" }}>{k}</span></span>)}
      </div>

      {/* Agent nodes */}
      <div className="relative flex flex-col gap-0">
        {/* Vertical spine */}
        <div className="absolute left-[19px] top-4 bottom-4 w-px bg-white/[0.05]" />

        {steps.map((s, i) => (
          <div key={s.name} className="flex flex-col">
            <div className="flex items-center gap-3 px-2 py-2.5 rounded-xl transition-all"
              style={{ background: `${s.color}08`, border: `1px solid ${s.color}20` }}>
              {/* Step circle */}
              <div className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 text-base z-10"
                style={{ background: `${s.color}15`, border: `1px solid ${s.color}35` }}>
                {s.icon}
              </div>
              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-white text-xs font-semibold">{s.name}</span>
                  {s.ext && (
                    <span className="text-[9px] px-1.5 py-0.5 rounded font-mono"
                      style={{ background: "#10B98112", color: "#10B981", border: "1px solid #10B98130" }}>
                      + {s.ext}
                    </span>
                  )}
                </div>
                <p className="text-[10px] mt-0.5 font-mono" style={{ color: `${s.color}99` }}>
                  → {s.out}
                </p>
              </div>
              {/* Step number */}
              <div className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0"
                style={{ background: `${s.color}20`, color: s.color }}>
                {i + 1}
              </div>
            </div>
            {i < steps.length - 1 && (
              <div className="flex pl-[22px] my-0.5">
                <div className="flex flex-col items-center gap-0.5">
                  <div className="w-px h-1.5 bg-white/[0.05]" />
                  <ArrowRight size={10} className="text-slate-700 rotate-90" />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function DocsPage() {
  const [expandedAgent, setExpandedAgent] = useState(null);

  const toggle = (id) => setExpandedAgent(prev => prev === id ? null : id);

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 pb-20 flex flex-col gap-8">

      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <div className="glass rounded-2xl p-6" style={{ border: "1px solid rgba(139,92,246,0.2)" }}>
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ background: "rgba(139,92,246,0.15)", border: "1px solid rgba(139,92,246,0.3)" }}>
              <FileText size={22} className="text-accent-purple" />
            </div>
            <div>
              <h1 className="text-white font-black text-xl tracking-tight">
                System Architecture
              </h1>
              <p className="text-slate-400 text-sm mt-1 leading-relaxed">
                FinanceIQ is a full-stack AI financial coach built on a React frontend, Node.js/Express API,
                and a Python LangGraph multi-agent pipeline connected to OpenRouter and Tavily.
              </p>
              <div className="flex flex-wrap gap-2 mt-3">
                {["React 18", "Node.js", "LangGraph", "OpenRouter", "Tavily", "SSE"].map(t => (
                  <span key={t} className="text-[10px] px-2.5 py-1 rounded-full glass text-slate-300 border border-white/[0.08] font-mono">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* ── System architecture diagram ────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.04 }}>
        <SectionTitle icon={Server} label="System Architecture Diagram" color="#8B5CF6" />
        <Card>
          <ArchDiagram />
        </Card>
      </motion.div>

      {/* ── Agent pipeline visual ──────────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.06 }}>
        <SectionTitle icon={Brain} label="LangGraph Agent Pipeline" color="#EC4899" />
        <Card>
          <p className="text-slate-500 text-[11px] mb-4 leading-relaxed">
            Six specialist agents run sequentially inside a <span className="text-pink-400 font-mono">StateGraph</span>.
            Each agent enriches the shared <span className="text-purple-400 font-mono">FinancialState</span> and passes it forward.
            No agent calls another directly — all communication is through state.
          </p>
          <PipelineDiagram />
        </Card>
      </motion.div>

      {/* ── Data flow ─────────────────────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
        <SectionTitle icon={ArrowRight} label="End-to-End Data Flow" color="#06B6D4" />
        <Card>
          <div className="flex flex-col gap-2">
            {FLOW_STEPS.map(({ icon: Icon, label, detail, color }, i) => (
              <div key={label} className="flex items-center gap-3">
                {/* Step bubble */}
                <div className="flex flex-col items-center flex-shrink-0" style={{ width: 32 }}>
                  <div className="w-8 h-8 rounded-full flex items-center justify-center"
                    style={{ background: color + "18", border: `1px solid ${color}35` }}>
                    <Icon size={13} style={{ color }} />
                  </div>
                  {i < FLOW_STEPS.length - 1 && (
                    <div className="w-px h-3 mt-0.5" style={{ background: color + "25" }} />
                  )}
                </div>
                {/* Label */}
                <div className="flex-1 pb-2 border-b border-white/[0.04] last:border-0">
                  <div className="flex items-baseline gap-2">
                    <span className="text-white text-xs font-semibold">{label}</span>
                    <span className="text-slate-500 text-[11px]">{detail}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </motion.div>

      {/* ── Agent pipeline ────────────────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.08 }}>
        <SectionTitle icon={Brain} label="Agent Pipeline (LangGraph)" color="#8B5CF6" />
        <div className="glass rounded-2xl p-4">
          <p className="text-slate-400 text-xs mb-4 leading-relaxed px-1">
            Six specialist agents run sequentially inside a LangGraph <code className="text-accent-purple font-mono text-[10px]">StateGraph</code>.
            Each agent receives the full accumulated state, enriches it, and passes it forward.
            Click any agent to see its inputs and outputs.
          </p>
          <div className="flex flex-col">
            {AGENTS.map((agent, i) => (
              <AgentNode
                key={agent.id}
                agent={agent}
                index={i}
                expanded={expandedAgent === agent.id}
                onToggle={() => toggle(agent.id)}
              />
            ))}
          </div>
          {/* LangGraph state schema note */}
          <div className="mt-4 p-3 rounded-xl text-[11px] text-slate-400 leading-relaxed"
            style={{ background: "rgba(139,92,246,0.05)", border: "1px solid rgba(139,92,246,0.12)" }}>
            <span className="text-accent-purple font-semibold">FinancialState</span> keys:
            {" "}raw_data · financial_snapshot · health_score · financial_insights · debt_plan · savings_plan · budget_recommendations · final_report · charts · errors
          </div>
        </div>
      </motion.div>

      {/* ── Tech stack ────────────────────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <SectionTitle icon={Server} label="Tech Stack" color="#06B6D4" />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {STACK.map(({ layer, icon: Icon, color, items }) => (
            <div key={layer} className="glass rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-6 h-6 rounded-lg flex items-center justify-center"
                  style={{ background: color + "18", border: `1px solid ${color}30` }}>
                  <Icon size={12} style={{ color }} />
                </div>
                <span className="text-white text-xs font-bold">{layer}</span>
              </div>
              <div className="flex flex-col gap-1.5">
                {items.map(({ name, note }) => (
                  <div key={name} className="flex items-baseline gap-2">
                    <span className="w-1 h-1 rounded-full flex-shrink-0 mt-1.5" style={{ background: color }} />
                    <span className="text-slate-200 text-[11px] font-medium">{name}</span>
                    <span className="text-slate-600 text-[10px]">{note}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* ── Protocols & integrations (MCP-style) ─────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12 }}>
        <SectionTitle icon={Zap} label="Protocols & Integrations" color="#F59E0B" />
        <div className="flex flex-col gap-3">
          {MCP_ITEMS.map(({ title, icon: Icon, color, body, tags = [] }) => (
            <div key={title} className="glass rounded-xl p-4">
              <div className="flex items-center gap-2.5 mb-2">
                <div className="w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ background: color + "18", border: `1px solid ${color}30` }}>
                  <Icon size={12} style={{ color }} />
                </div>
                <span className="text-white text-sm font-semibold">{title}</span>
              </div>
              <p className="text-slate-400 text-xs leading-relaxed pl-8 mb-2">{body}</p>
              {tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pl-8">
                  {tags.map(t => (
                    <span key={t} className="text-[9px] px-2 py-0.5 rounded-full font-mono"
                      style={{ background: color + "12", color: color + "cc", border: `1px solid ${color}20` }}>
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </motion.div>

      {/* ── Models ────────────────────────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.14 }}>
        <SectionTitle icon={Brain} label="Supported Models (via OpenRouter)" color="#8B5CF6" />
        <Card>
          <p className="text-slate-500 text-[11px] mb-4">
            All models are accessed through OpenRouter's unified API. Switch models in Config — no code changes needed.
          </p>
          <div className="flex flex-col gap-2">
            {MODELS.map(({ name, provider, speed, accuracy, cost, tag, emoji }) => (
              <div key={name} className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                <span className="text-lg flex-shrink-0">{emoji}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-white text-xs font-semibold">{name}</span>
                    <span className="text-[9px] text-slate-500">{provider}</span>
                    {tag && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded-full font-medium"
                        style={{ background: "rgba(139,92,246,0.12)", color: "#A78BFA", border: "1px solid rgba(139,92,246,0.2)" }}>
                        {tag}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 mt-1.5">
                    <div className="flex items-center gap-1">
                      <span className="text-[9px] text-slate-600 w-10">Speed</span>
                      <MiniBar value={speed} color="#06B6D4" />
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="text-[9px] text-slate-600 w-10">Accuracy</span>
                      <MiniBar value={accuracy} color="#8B5CF6" />
                    </div>
                  </div>
                </div>
                <span className="text-[10px] font-mono text-slate-500 flex-shrink-0">{cost}</span>
              </div>
            ))}
          </div>
        </Card>
      </motion.div>

      {/* ── Security & privacy ────────────────────────────────────────────── */}
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.16 }}>
        <SectionTitle icon={Shield} label="Security & Privacy" color="#10B981" />
        <Card>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              { title: "Keys in browser only", body: "API keys are stored in localStorage via Zustand persist. They are never logged server-side.", color: "#10B981" },
              { title: "Files deleted on close", body: "Uploaded files are written to /server/uploads/ and deleted immediately after analysis completes.", color: "#06B6D4" },
              { title: "No server-side storage", body: "Analysis results exist only in the client's Zustand store. Nothing is persisted to a database.", color: "#8B5CF6" },
              { title: "Direct API calls", body: "Requests go directly from the Python process to OpenRouter and Tavily. No middleware reads the content.", color: "#F59E0B" },
            ].map(({ title, body, color }) => (
              <div key={title} className="flex items-start gap-2.5 p-3 rounded-xl bg-white/[0.02]">
                <CheckCircle2 size={14} className="flex-shrink-0 mt-0.5" style={{ color }} />
                <div>
                  <p className="text-white text-xs font-semibold">{title}</p>
                  <p className="text-slate-500 text-[11px] mt-0.5 leading-relaxed">{body}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </motion.div>

    </div>
  );
}
