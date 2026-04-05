import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { useDropzone } from "react-dropzone";
import { useFinancialStore } from "../../store/financialStore.js";
import { fmt } from "../../utils/formatters.js";
import { AGENT_ORDER } from "../../store/financialStore.js";

// ── Typing indicator ──────────────────────────────────────────────────────
export function TypingIndicator() {
  return (
    <div className="flex items-end gap-2.5 mb-3">
      <BotAvatar />
      <div className="chat-bubble-bot px-4 py-3 flex gap-1.5 items-center">
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
      </div>
    </div>
  );
}

// ── Bot avatar ────────────────────────────────────────────────────────────
function BotAvatar() {
  return (
    <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mb-0.5"
      style={{ background: "linear-gradient(135deg,#7c3aed,#3b82f6)", boxShadow: "0 0 10px rgba(124,58,237,0.4)" }}
    >
      <Sparkles size={13} className="text-white" />
    </div>
  );
}

// ── File upload widget (inside chat) ──────────────────────────────────────
function InlineFileUpload({ onUploaded }) {
  const { file, setFile } = useFinancialStore();

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (accepted) => { if (accepted[0]) { setFile(accepted[0]); onUploaded?.(accepted[0]); } },
    accept: { "text/csv": [".csv"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"], "application/vnd.ms-excel": [".xls"] },
    maxFiles: 1,
  });

  if (file) {
    return (
      <div className="flex items-center gap-3 mt-3 px-3 py-2.5 rounded-xl"
        style={{ background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.25)" }}
      >
        <span className="text-green-400 text-lg">✓</span>
        <div className="min-w-0">
          <p className="text-white text-xs font-medium truncate">{file.name}</p>
          <p className="text-slate-500 text-[10px]">{(file.size / 1024).toFixed(1)} KB · Ready</p>
        </div>
        <button onClick={() => setFile(null)} className="ml-auto text-slate-500 hover:text-slate-300 text-xs">✕</button>
      </div>
    );
  }

  return (
    <div className="mt-3 flex flex-col gap-2">
      {/* Drop zone */}
      <div
        {...getRootProps()}
        className="rounded-xl px-4 py-5 text-center cursor-pointer transition-all"
        style={{
          border: `2px dashed ${isDragActive ? "rgba(139,92,246,0.7)" : "rgba(139,92,246,0.3)"}`,
          background: isDragActive ? "rgba(139,92,246,0.08)" : "rgba(139,92,246,0.03)",
        }}
      >
        <input {...getInputProps()} />
        <div className="text-2xl mb-1.5">📁</div>
        <p className="text-white text-xs font-semibold mb-0.5">
          {isDragActive ? "Drop your file here!" : "Click to upload your file"}
        </p>
        <p className="text-slate-500 text-[10px]">
          Supports Excel (.xlsx, .xls) and CSV — max 10 MB
        </p>
      </div>

      {/* Sample download row */}
      <div className="flex items-center gap-1.5 px-1">
        <span className="text-slate-600 text-[10px]">No file yet?</span>
        <a
          href="/api/sample?fmt=xlsx"
          download="sample_transactions.xlsx"
          className="text-accent-purple text-[10px] font-medium hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          Download sample Excel
        </a>
        <span className="text-slate-700 text-[10px]">·</span>
        <a
          href="/api/sample?fmt=csv"
          download="sample_transactions.csv"
          className="text-slate-500 text-[10px] hover:text-slate-300 hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          CSV
        </a>
      </div>
    </div>
  );
}

// ── Verbose agent descriptions shown while running ────────────────────────
const AGENT_VERBOSE = {
  document_ingestion: {
    running: "📂 Reading your transactions… classifying each row as income, expense, transfer, or refund. Building your complete financial picture.",
    done:    "✅ File ingested — transactions parsed and categorized.",
  },
  financial_analyzer: {
    running: "🧠 The AI is now studying your spending patterns, income sources, and savings behavior to compute your personal Financial Health Score (0–100) and identify key insights.",
    done:    "✅ Financial health scored — insights identified.",
  },
  debt_strategist: {
    running: "💳 Scanning for credit card payments, loans, and debt signals. Calculating the best payoff strategy — Avalanche (saves most interest) or Snowball (fastest psychological wins).",
    done:    "✅ Debt strategy built — payoff plan ready.",
  },
  savings_strategy: {
    running: "🏦 Calculating your emergency fund target (3–6 months of expenses), defining savings goals, and searching for the best high-yield savings accounts near you.",
    done:    "✅ Savings plan designed — goals and targets set.",
  },
  budget_advisor: {
    running: "📊 Analyzing every spending category. Identifying where you're overspending and recommending realistic 5–15% reductions to free up extra cash each month.",
    done:    "✅ Budget optimized — category allocations ready.",
  },
  report_generator: {
    running: "📋 Pulling everything together — compiling your personalized financial report, generating charts, and writing your wealth-building action plan.",
    done:    "✅ Report generated — your full analysis is ready!",
  },
};

// ── Progress step inside chat ─────────────────────────────────────────────
function ProgressMessage({ steps, progress }) {
  const doneCount = steps.filter(s => s.status === "done").length;
  const current = steps.find(s => s.status === "running");
  const total = AGENT_ORDER.length;

  return (
    <div className="mt-3 flex flex-col gap-3">
      {/* Overall bar */}
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between">
          <span className="text-[11px] text-slate-400 font-medium">
            {current
              ? `Agent ${doneCount + 1} of ${total} running…`
              : doneCount === total
              ? "All agents complete!"
              : "Starting agents…"}
          </span>
          <span className="text-xs font-mono text-accent-purple font-bold">{Math.round(progress)}%</span>
        </div>
        <div className="progress-bar"><div className="progress-fill" style={{ width: `${progress}%` }} /></div>
      </div>

      {/* Current agent verbose message */}
      {current && AGENT_VERBOSE[current.agent] && (
        <div className="flex items-start gap-2 px-3 py-2.5 rounded-xl"
          style={{ background: "rgba(139,92,246,0.08)", border: "1px solid rgba(139,92,246,0.2)" }}
        >
          <span className="animate-pulse text-sm flex-shrink-0">{current.icon}</span>
          <p className="text-slate-300 text-[11px] leading-relaxed">
            {AGENT_VERBOSE[current.agent].running}
          </p>
        </div>
      )}

      {/* Step list */}
      <div className="flex flex-col gap-1.5">
        {AGENT_ORDER.map((agent) => {
          const s = steps.find(x => x.agent === agent);
          const isDone = s?.status === "done";
          const isRunning = s?.status === "running";
          const isPending = !s || s.status === "pending";
          const verboseInfo = AGENT_VERBOSE[agent] || {};

          return (
            <div key={agent}
              className="flex items-start gap-2.5 px-3 py-2 rounded-lg transition-all"
              style={{
                background: isDone ? "rgba(16,185,129,0.06)" : isRunning ? "rgba(139,92,246,0.08)" : "transparent",
                border: isDone ? "1px solid rgba(16,185,129,0.18)" : isRunning ? "1px solid rgba(139,92,246,0.2)" : "1px solid transparent",
              }}
            >
              {/* Status icon */}
              <span className="text-sm flex-shrink-0 mt-0.5">
                {isDone ? "✅" : isRunning ? <span className="animate-pulse">{s?.icon}</span> : "⏳"}
              </span>
              <div className="flex-1 min-w-0">
                <p className={`text-[11px] font-semibold ${isDone ? "text-green-400" : isRunning ? "text-purple-300" : "text-slate-600"}`}>
                  {agent.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}
                </p>
                {isDone && verboseInfo.done && (
                  <p className="text-[10px] text-green-500/70 mt-0.5">{verboseInfo.done}</p>
                )}
                {/* Show summary when done */}
                {isDone && s?.summary && Object.keys(s.summary).length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {Object.entries(s.summary).map(([k, v]) =>
                      v != null ? (
                        <span key={k} className="text-[9px] px-1.5 py-0.5 rounded bg-white/[0.04] text-slate-400 border border-white/[0.06] font-mono">
                          {k.replace(/_/g, " ")}: {String(v)}
                        </span>
                      ) : null
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Result summary card inside chat ──────────────────────────────────────
function ResultCard({ result, onViewDashboard }) {
  const snap = result?.financial_snapshot || {};
  const score = result?.health_score;
  const color = score >= 70 ? "#10b981" : score >= 50 ? "#f59e0b" : "#ef4444";
  const label = score >= 90 ? "Excellent" : score >= 70 ? "Good" : score >= 50 ? "Fair" : "Needs Work";

  return (
    <div className="mt-3 flex flex-col gap-3">
      {/* Score banner */}
      <div className="flex items-center gap-3 px-4 py-3 rounded-xl"
        style={{ background: `${color}12`, border: `1px solid ${color}30` }}
      >
        <span className="text-3xl font-black font-mono" style={{ color }}>{Math.round(score || 0)}</span>
        <div>
          <p className="text-white font-semibold text-sm">Financial Health: {label}</p>
          <p className="text-slate-400 text-xs">{snap.transaction_count || 0} transactions analyzed</p>
        </div>
      </div>

      {/* Mini metrics */}
      <div className="grid grid-cols-3 gap-2">
        {[
          { label: "Income",   value: fmt.compact(snap.total_income),   c: "#10b981" },
          { label: "Expenses", value: fmt.compact(snap.total_expenses),  c: "#ef4444" },
          { label: "Savings%", value: fmt.pct(snap.savings_rate),        c: "#8b5cf6" },
        ].map(m => (
          <div key={m.label} className="text-center px-2 py-2 rounded-xl bg-white/[0.03] border border-white/[0.06]">
            <p className="font-mono font-bold text-sm" style={{ color: m.c }}>{m.value}</p>
            <p className="text-slate-500 text-[10px]">{m.label}</p>
          </div>
        ))}
      </div>

      <button onClick={onViewDashboard} className="btn-primary w-full text-sm flex items-center justify-center gap-2 py-2.5">
        View Full Dashboard →
      </button>
    </div>
  );
}

// ── Main ChatMessage renderer ─────────────────────────────────────────────
export default function ChatMessage({ msg, onFileUploaded, onViewDashboard }) {
  const isBot = msg.role === "bot";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className={`flex items-end gap-2.5 mb-3 ${isBot ? "" : "flex-row-reverse"}`}
    >
      {isBot && <BotAvatar />}

      <div className={`max-w-[82%] ${isBot ? "chat-bubble-bot" : "chat-bubble-user"} px-4 py-3`}>
        {/* Text */}
        <p className="text-sm leading-relaxed text-slate-200">{msg.content}</p>

        {/* Upload prompt — actual widget is the sticky UploadBar at the bottom */}
        {msg.type === "upload" && (
          <div className="mt-2 flex items-center gap-2 text-[11px] text-slate-500">
            <span>⬇️</span>
            <span>Use the upload bar below to select your file.</span>
          </div>
        )}

        {/* Progress */}
        {msg.type === "progress" && msg.meta && (
          <ProgressMessage steps={msg.meta.steps} progress={msg.meta.progress} />
        )}

        {/* Result */}
        {msg.type === "result" && msg.meta && (
          <ResultCard result={msg.meta.result} onViewDashboard={onViewDashboard} />
        )}

        {/* Timestamp */}
        <p className="text-[10px] text-slate-600 mt-1.5 text-right">
          {new Date(msg.id).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </p>
      </div>

      {!isBot && (
        <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mb-0.5 bg-white/[0.06] border border-white/10 text-xs">
          👤
        </div>
      )}
    </motion.div>
  );
}
