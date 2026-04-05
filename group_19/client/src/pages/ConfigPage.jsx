import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Eye, EyeOff, CheckCircle2, ChevronDown, ChevronRight, Info, Sliders, Key, Zap, Mail } from "lucide-react";
import { useFinancialStore, MODELS } from "../store/financialStore.js";

// ── Rich model catalogue ──────────────────────────────────────────────────
// MODEL_INFO — exactly mirrors MODELS, no more, no less
const MODEL_INFO = {
  "openai/gpt-4o-mini": {
    emoji: "⚡",
    tagline: "Fast, reliable, excellent JSON output",
    plain: "The default choice. Handles all 6 financial agents reliably, returns well-structured JSON every time, and costs fractions of a cent per analysis.",
    strengths: ["Most reliable JSON", "Ultra-fast", "Best value"],
    best_for: "Most users — start here",
    speed: 95, accuracy: 78, cost: 95,
  },
  "openai/gpt-4o": {
    emoji: "🧠",
    tagline: "Deepest financial reasoning",
    plain: "OpenAI's flagship. Catches nuances and edge cases others miss — best for complex portfolios with many categories or unusual transactions.",
    strengths: ["Highest accuracy", "Deep reasoning", "Complex scenarios"],
    best_for: "Power users with complex finances",
    speed: 70, accuracy: 95, cost: 60,
  },
  "openai/gpt-4-turbo": {
    emoji: "🚀",
    tagline: "GPT-4 accuracy, faster",
    plain: "Near-GPT-4o accuracy at higher speed. Great when you want thorough analysis without waiting.",
    strengths: ["High accuracy", "Faster than GPT-4o", "128K context"],
    best_for: "Users wanting depth and speed",
    speed: 80, accuracy: 92, cost: 55,
  },
  "anthropic/claude-3.5-sonnet": {
    emoji: "🎯",
    tagline: "Best report writing quality",
    plain: "Claude produces the most polished, readable reports. If the written output quality matters, this is your model.",
    strengths: ["Crystal-clear writing", "Logical structure", "Reliable JSON"],
    best_for: "Users who want the most readable reports",
    speed: 75, accuracy: 93, cost: 58,
  },
  "anthropic/claude-3.5-haiku": {
    emoji: "💨",
    tagline: "Claude quality at low cost",
    plain: "Anthropic's fastest model — same clear writing style as Sonnet at a fraction of the price.",
    strengths: ["Very fast", "Clear writing", "Cheapest Claude"],
    best_for: "Quick analyses on a budget",
    speed: 94, accuracy: 80, cost: 88,
  },
  "deepseek/deepseek-chat": {
    emoji: "🔍",
    tagline: "GPT-4 quality at 10× lower cost",
    plain: "DeepSeek V3 rivals GPT-4o for financial reasoning at a fraction of the price. The best bang-for-buck paid model.",
    strengths: ["GPT-4 level accuracy", "Very cheap", "Strong JSON output"],
    best_for: "Cost-conscious users who want accuracy",
    speed: 72, accuracy: 92, cost: 90,
  },
  "google/gemini-flash-1.5": {
    emoji: "✨",
    tagline: "Google speed with large context",
    plain: "Gemini Flash is very fast with a massive context window — ideal for long transaction histories spanning many months.",
    strengths: ["Very fast", "Large context window", "Google reliability"],
    best_for: "Large datasets with many transactions",
    speed: 93, accuracy: 74, cost: 82,
  },
  "google/gemini-pro-1.5": {
    emoji: "🌟",
    tagline: "1 million token context",
    plain: "Gemini Pro 1.5 can fit an entire year of detailed transactions in one call. Best for users with very large or complex datasets.",
    strengths: ["1M token context", "Balanced accuracy", "Multi-modal"],
    best_for: "Very large datasets",
    speed: 78, accuracy: 85, cost: 72,
  },
  // ── Free models (throttled: 10 s between agents ≈ 60 s total) ─────────────
  "nvidia/nemotron-3-super-120b-a12b:free": {
    emoji: "🟢",
    tagline: "Free · 120B · JSON + reasoning + tools",
    plain: "NVIDIA's 120B MoE model — the strongest free option on OpenRouter. Full JSON-schema enforcement, 262K context, and native reasoning. Pipeline takes ~60 s due to rate-limit throttling (10 s per agent).",
    strengths: ["JSON schema enforced", "262K context", "Full tool-calling", "Reasoning mode"],
    best_for: "Free users who want maximum quality",
    speed: 45, accuracy: 91, cost: 100,
  },
  "arcee-ai/trinity-mini:free": {
    emoji: "⚡",
    tagline: "Free · 26B MoE · fastest free model",
    plain: "Arcee Trinity Mini uses 3B active parameters per token from a 26B pool — fast inference with full JSON schema and function calling. Best free option when you want speed over raw size.",
    strengths: ["Fastest free model", "JSON schema enforced", "Function calling", "Reasoning mode"],
    best_for: "Free users who want fast results",
    speed: 72, accuracy: 82, cost: 100,
  },
  "minimax/minimax-m2.5:free": {
    emoji: "📊",
    tagline: "Free · Large MoE · trained on spreadsheet/office workflows",
    plain: "MiniMax M2.5 is explicitly trained on office, spreadsheet, and data tasks — making it unusually well-suited for financial analysis. 196K context with JSON mode and reasoning.",
    strengths: ["Office/data trained", "196K context", "JSON mode", "Reasoning mode"],
    best_for: "Free users with spreadsheet-heavy data",
    speed: 55, accuracy: 88, cost: 100,
  },
  "qwen/qwen3-next-80b-a3b-instruct:free": {
    emoji: "🚀",
    tagline: "Free · 80B MoE · high-throughput JSON",
    plain: "Qwen3 80B A3B runs 3B active parameters from an 80B pool for high throughput. Full JSON schema enforcement and structured outputs — no reasoning chain but very consistent output.",
    strengths: ["JSON schema enforced", "262K context", "High throughput", "Consistent output"],
    best_for: "Free users who want reliable structured JSON",
    speed: 68, accuracy: 84, cost: 100,
  },
};

function MiniBar({ value, color }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className="flex-1 h-1 rounded-full bg-white/[0.06] overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${value}%`, background: color }} />
      </div>
      <span className="text-[10px] font-mono text-slate-500 w-6 text-right">{value}</span>
    </div>
  );
}

function ModelCard({ m, isSelected, onSelect }) {
  const [expanded, setExpanded] = useState(false);
  const info = MODEL_INFO[m.value] || {};

  return (
    <div
      className={`rounded-xl overflow-hidden transition-all duration-200 cursor-pointer ${
        isSelected ? "ring-1 ring-accent-purple/60" : ""
      }`}
      style={{
        background: isSelected ? "rgba(139,92,246,0.08)" : "rgba(255,255,255,0.025)",
        border: isSelected ? "1px solid rgba(139,92,246,0.3)" : "1px solid rgba(255,255,255,0.07)",
      }}
      onClick={() => onSelect(m.value)}
    >
      <div className="flex items-center gap-3 px-4 py-3">
        <span className="text-xl flex-shrink-0">{info.emoji || "🤖"}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-white text-sm font-semibold">{m.label}</p>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/[0.06] text-slate-400">{m.tag}</span>
          </div>
          {info.tagline && <p className="text-slate-400 text-xs mt-0.5">{info.tagline}</p>}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {isSelected && <CheckCircle2 size={15} className="text-accent-purple" />}
          <button
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
            className="text-slate-500 hover:text-slate-300 transition-colors p-1"
          >
            {expanded ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22 }}
            className="overflow-hidden border-t border-white/[0.05]"
          >
            <div className="px-4 py-3 flex flex-col gap-3">
              {/* Plain English explanation */}
              <div className="flex items-start gap-2 p-3 rounded-lg bg-white/[0.03]">
                <Info size={13} className="text-accent-cyan mt-0.5 flex-shrink-0" />
                <p className="text-slate-300 text-xs leading-relaxed">{info.plain}</p>
              </div>

              {/* Performance bars */}
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <p className="text-[10px] text-slate-500 mb-1">Speed</p>
                  <MiniBar value={info.speed} color="#06b6d4" />
                </div>
                <div>
                  <p className="text-[10px] text-slate-500 mb-1">Accuracy</p>
                  <MiniBar value={info.accuracy} color="#8b5cf6" />
                </div>
                <div>
                  <p className="text-[10px] text-slate-500 mb-1">Cost eff.</p>
                  <MiniBar value={info.cost} color="#10b981" />
                </div>
              </div>

              {/* Strengths */}
              <div className="flex flex-wrap gap-1.5">
                {(info.strengths || []).map(s => (
                  <span key={s} className="text-[10px] px-2 py-0.5 rounded-full bg-white/[0.04] text-slate-400 border border-white/[0.06]">
                    ✓ {s}
                  </span>
                ))}
              </div>

              <p className="text-[10px] text-slate-500">
                <span className="text-accent-purple">Best for:</span> {info.best_for}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function SecretInput({ label, value, onChange, placeholder, hint }) {
  const [show, setShow] = useState(false);
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-slate-400 text-xs font-medium">{label}</label>
      <div className="relative">
        <input
          type={show ? "text" : "password"}
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          className="field-input pr-10"
        />
        <button type="button" onClick={() => setShow(!show)}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
        >
          {show ? <EyeOff size={14} /> : <Eye size={14} />}
        </button>
      </div>
      {hint && <p className="text-slate-600 text-[10px]">{hint}</p>}
    </div>
  );
}

function SliderField({ label, value, onChange, min, max, step = 0.05, description }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <label className="text-slate-400 text-xs font-medium">{label}</label>
        <span className="text-white font-mono text-xs bg-white/[0.05] px-2 py-0.5 rounded">{value.toFixed(2)}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step}
        value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
        style={{
          background: `linear-gradient(90deg, #7c3aed ${((value - min) / (max - min)) * 100}%, rgba(255,255,255,0.1) ${((value - min) / (max - min)) * 100}%)`,
        }}
      />
      <p className="text-slate-600 text-[10px] leading-relaxed">{description}</p>
    </div>
  );
}

const AGENT_DESCRIPTIONS = [
  { icon: "📂", name: "Document Ingestion", desc: "Reads your transaction file and classifies every row as income, expense, transfer, or refund. Builds the financial picture before any AI runs." },
  { icon: "🧠", name: "Financial Analyzer", desc: "Computes your Financial Health Score (0–100) and generates 4–8 personalized insights about your spending patterns and financial behavior." },
  { icon: "💳", name: "Debt Strategist", desc: "Detects debt signals in your transactions and recommends the best payoff strategy — Avalanche (save most interest) or Snowball (fastest wins)." },
  { icon: "🏦", name: "Savings Strategist", desc: "Sets your emergency fund target (3–6 months expenses), defines savings goals, and searches live bank rates for the best accounts." },
  { icon: "📊", name: "Budget Advisor", desc: "Analyzes every spending category, flags overspending, and recommends realistic 5–15% reductions to free up cash each month." },
  { icon: "📋", name: "Report Generator", desc: "Synthesizes all agent outputs into a comprehensive Markdown report plus interactive charts — your personal financial playbook." },
];

export default function ConfigPage() {
  const { config, setConfig } = useFinancialStore();
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [infoOpen, setInfoOpen] = useState(false);
  const temperature = config.temperature ?? 0.1;
  const setTemperature = (v) => setConfig({ temperature: v });

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      {/* Header */}
      <div className="px-5 py-4 border-b border-white/[0.05] flex items-center justify-between">
        <div>
          <h2 className="text-white font-bold text-base">Configuration</h2>
          <p className="text-slate-500 text-xs mt-0.5">Changes save automatically as you type</p>
        </div>
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium"
          style={{ background: "rgba(16,185,129,0.06)", border: "1px solid rgba(16,185,129,0.15)", color: "#34d399" }}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
          Auto-saved
        </div>
      </div>

      {/* Missing key banner */}
      {(!config.openrouterKey || !config.tavilyKey) && (
        <div className="mx-4 mt-4 px-4 py-3 rounded-xl flex items-start gap-3"
          style={{ background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.3)" }}
        >
          <span className="text-amber-400 text-lg flex-shrink-0">⚠️</span>
          <div>
            <p className="text-amber-300 text-xs font-semibold">API keys required</p>
            <p className="text-slate-400 text-xs mt-0.5">
              {!config.openrouterKey && <span>OpenRouter key missing — get one free at <a href="https://openrouter.ai/keys" target="_blank" rel="noreferrer" className="text-amber-400 hover:underline">openrouter.ai/keys</a>. </span>}
              {!config.tavilyKey && <span>Tavily key missing — get one free at <a href="https://tavily.com" target="_blank" rel="noreferrer" className="text-amber-400 hover:underline">tavily.com</a>.</span>}
            </p>
          </div>
        </div>
      )}

      <div className="flex flex-col gap-5 px-4 py-5 pb-24">

        {/* ── API Keys ──────────────────────────────────────────────────── */}
        <section>
          <div className="flex items-center gap-2 mb-3">
            <Key size={14} className="text-accent-purple" />
            <h3 className="text-white font-semibold text-sm">API Keys</h3>
          </div>
          <div className="flex flex-col gap-3">
            <SecretInput
              label="OpenRouter API Key *"
              value={config.openrouterKey}
              onChange={v => setConfig({ openrouterKey: v })}
              placeholder="sk-or-v1-..."
              hint="Required · Get your key free at openrouter.ai · Unlocks all AI models below"
            />
            <SecretInput
              label="Tavily API Key *"
              value={config.tavilyKey}
              onChange={v => setConfig({ tavilyKey: v })}
              placeholder="tvly-..."
              hint="Required · Enables live market & savings research · Get free at tavily.com"
            />
          </div>
        </section>

        {/* ── Model Selection ───────────────────────────────────────────── */}
        <section>
          <div className="flex items-center gap-2 mb-1">
            <Zap size={14} className="text-accent-cyan" />
            <h3 className="text-white font-semibold text-sm">AI Model</h3>
          </div>
          <p className="text-slate-500 text-xs mb-3 leading-relaxed">
            The model is the "brain" reading your transactions.{" "}
            <span className="text-accent-purple">GPT-4o Mini</span> is the recommended default — instant, reliable, excellent JSON.{" "}
            Free models work too — the pipeline auto-throttles to{" "}
            <span className="text-accent-cyan">10 s between agents</span> to stay within rate limits (~60 s total).{" "}
            Best free pick: <span className="text-accent-cyan">NVIDIA Nemotron 120B</span> — full JSON schema + reasoning.
          </p>

          {/* Dropdown */}
          <div className="relative mb-3">
            <select
              value={config.model}
              onChange={e => setConfig({ model: e.target.value })}
              className="field-input appearance-none pr-8 cursor-pointer"
            >
              {MODELS.map(m => (
                <option key={m.value} value={m.value} className="bg-bg-card text-white">
                  {m.label}  ·  {m.tag}
                </option>
              ))}
            </select>
            <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          </div>

          {/* Selected model detail card (always visible) */}
          {(() => {
            const m = MODELS.find(x => x.value === config.model);
            const info = MODEL_INFO[config.model] || {};
            if (!m) return null;
            return (
              <div className="glass rounded-xl overflow-hidden">
                <div className="flex items-center gap-3 px-4 py-3 border-b border-white/[0.05]">
                  <span className="text-2xl">{info.emoji || "🤖"}</span>
                  <div>
                    <p className="text-white font-semibold text-sm">{m.label}
                      <span className="ml-2 text-[10px] text-slate-500 font-normal">{m.tag}</span>
                    </p>
                    <p className="text-accent-cyan text-xs mt-0.5">{info.tagline}</p>
                  </div>
                </div>
                <div className="px-4 py-3 flex flex-col gap-3">
                  <div className="flex items-start gap-2 p-3 rounded-lg bg-white/[0.03]">
                    <Info size={12} className="text-accent-cyan mt-0.5 flex-shrink-0" />
                    <p className="text-slate-300 text-xs leading-relaxed">{info.plain}</p>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    {[["Speed", info.speed, "#06b6d4"], ["Accuracy", info.accuracy, "#8b5cf6"], ["Cost eff.", info.cost, "#10b981"]].map(([lbl, val, c]) => (
                      <div key={lbl}>
                        <p className="text-[10px] text-slate-500 mb-1">{lbl}</p>
                        <MiniBar value={val} color={c} />
                      </div>
                    ))}
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {(info.strengths || []).map(s => (
                      <span key={s} className="text-[10px] px-2 py-0.5 rounded-full bg-white/[0.04] text-slate-400 border border-white/[0.06]">
                        ✓ {s}
                      </span>
                    ))}
                  </div>
                  <p className="text-[10px] text-slate-500">
                    <span className="text-accent-purple">Best for:</span> {info.best_for}
                  </p>
                </div>
              </div>
            );
          })()}
        </section>

        {/* ── Email Settings ────────────────────────────────────────────── */}
        <section>
          <div className="flex items-center gap-2 mb-3">
            <Mail size={14} className="text-accent-cyan" />
            <h3 className="text-white font-semibold text-sm">Email Settings</h3>
            <span className="text-[10px] text-slate-400 bg-white/[0.06] border border-white/[0.08] px-2 py-0.5 rounded-full">Brevo</span>
          </div>
          <div className="flex flex-col gap-3">
            <div className="p-3 rounded-xl bg-cyan-500/[0.06] border border-cyan-500/[0.2] text-xs text-slate-300 leading-relaxed">
              📧 Used to send financial reports by email. Get a free SMTP key at{" "}
              <a href="https://app.brevo.com" target="_blank" rel="noreferrer" className="text-cyan-400 hover:underline">app.brevo.com</a>
              {" "}→ SMTP &amp; API → SMTP tab.
            </div>
            <SecretInput
              label="Brevo SMTP Key"
              value={config.brevoApiKey || ""}
              onChange={v => setConfig({ brevoApiKey: v })}
              placeholder="xsmtpsib-..."
              hint="Your Brevo SMTP password — starts with xsmtpsib-"
            />
            <div className="flex flex-col gap-1.5">
              <label className="text-slate-400 text-xs font-medium">From Email Address</label>
              <input
                type="email"
                value={config.brevoFromEmail || ""}
                onChange={e => setConfig({ brevoFromEmail: e.target.value })}
                placeholder="you@yourdomain.com"
                className="field-input"
              />
              <p className="text-slate-500 text-[10px]">Must match the verified sender email in your Brevo account</p>
            </div>
          </div>
        </section>

        {/* ── Advanced Tuning ───────────────────────────────────────────── */}
        <section>
          <button
            onClick={() => setAdvancedOpen(!advancedOpen)}
            className="w-full flex items-center justify-between glass rounded-xl px-4 py-3 glass-hover"
          >
            <div className="flex items-center gap-2">
              <Sliders size={14} className="text-slate-400" />
              <span className="text-white text-sm font-medium">Advanced Tuning</span>
              <span className="text-[10px] text-slate-600 bg-white/[0.05] px-2 py-0.5 rounded-full">optional</span>
            </div>
            <ChevronDown size={14} className={`text-slate-400 transition-transform ${advancedOpen ? "rotate-180" : ""}`} />
          </button>

          <AnimatePresence>
            {advancedOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="flex flex-col gap-4 pt-3 px-1">
                  <div className="p-3 rounded-xl bg-blue-500/[0.06] border border-blue-500/[0.15] text-xs text-slate-300 leading-relaxed">
                    💡 <strong className="text-blue-300">For regular users:</strong> leave defaults. These controls are for developers or users who want to fine-tune the AI's behavior.
                  </div>

                  <SliderField
                    label="Temperature"
                    value={temperature}
                    onChange={setTemperature}
                    min={0} max={1} step={0.05}
                    description={`Controls how "creative" vs "precise" the AI is. Low (0.0–0.2) = factual and consistent, great for financial analysis. High (0.7+) = more varied and creative writing. Recommended: 0.10`}
                  />

                  <div className="grid grid-cols-3 gap-2 text-center">
                    {[
                      { label: "Conservative", val: 0.05, hint: "Most precise" },
                      { label: "Balanced", val: 0.1, hint: "Recommended ✓" },
                      { label: "Creative", val: 0.4, hint: "More varied" },
                    ].map(p => (
                      <button key={p.label}
                        onClick={() => setTemperature(p.val)}
                        className={`px-2 py-2 rounded-xl text-xs transition-all ${
                          temperature === p.val
                            ? "bg-accent-purple/20 text-white border border-accent-purple/40"
                            : "bg-white/[0.03] text-slate-400 border border-white/[0.07] hover:border-white/20"
                        }`}
                      >
                        <p className="font-semibold">{p.label}</p>
                        <p className="text-[10px] opacity-70 mt-0.5">{p.hint}</p>
                      </button>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </section>

        {/* ── How it works ──────────────────────────────────────────────── */}
        <section>
          <button
            onClick={() => setInfoOpen(!infoOpen)}
            className="w-full flex items-center justify-between glass rounded-xl px-4 py-3 glass-hover"
          >
            <div className="flex items-center gap-2">
              <Info size={14} className="text-slate-400" />
              <span className="text-white text-sm font-medium">How FinanceIQ Works</span>
            </div>
            <ChevronDown size={14} className={`text-slate-400 transition-transform ${infoOpen ? "rotate-180" : ""}`} />
          </button>

          <AnimatePresence>
            {infoOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="pt-3 flex flex-col gap-2">
                  {/* Plain English intro */}
                  <div className="glass rounded-xl p-4 text-xs text-slate-300 leading-relaxed"
                    style={{ borderLeft: "2px solid rgba(139,92,246,0.5)" }}
                  >
                    <p className="text-white font-semibold mb-2">🤖 What is a Multi-Agent AI System?</p>
                    <p>
                      Imagine hiring 6 financial experts simultaneously — each one specializing in a different topic.
                      That's exactly what FinanceIQ does. When you upload your transactions, 6 AI "agents" work in sequence,
                      each building on the previous one's findings. It's like getting a team of CFO, debt counselor, savings advisor,
                      budget planner, and report writer all in one click.
                    </p>
                  </div>

                  {/* Agent pipeline */}
                  {AGENT_DESCRIPTIONS.map((a, i) => (
                    <div key={i} className="flex items-start gap-3 px-4 py-3 glass rounded-xl">
                      <div className="flex flex-col items-center gap-1 flex-shrink-0">
                        <span className="text-lg">{a.icon}</span>
                        {i < AGENT_DESCRIPTIONS.length - 1 && (
                          <div className="w-px h-3 bg-white/[0.1]" />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-white text-xs font-semibold">Agent {i + 1}:</span>
                          <span className="text-accent-purple text-xs">{a.name}</span>
                        </div>
                        <p className="text-slate-400 text-[11px] mt-1 leading-relaxed">{a.desc}</p>
                      </div>
                    </div>
                  ))}

                  <div className="px-4 py-3 rounded-xl bg-green-500/[0.06] border border-green-500/[0.15] text-xs text-slate-300 leading-relaxed">
                    🏦 <strong className="text-green-400">Your data is private.</strong> Transactions are processed in memory and deleted immediately after analysis. Nothing is stored on our servers.
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </section>
      </div>
    </div>
  );
}
