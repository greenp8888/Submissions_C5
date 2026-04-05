import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, Loader2, Clock, AlertCircle } from "lucide-react";
import { useFinancialStore, AGENT_ORDER } from "../../store/financialStore.js";

const STEP_COLORS = {
  document_ingestion: "#06B6D4",
  financial_analyzer: "#8B5CF6",
  debt_strategist:    "#EF4444",
  savings_strategy:   "#10B981",
  budget_advisor:     "#F59E0B",
  report_generator:   "#3B82F6",
};

function StepItem({ step, index, totalCompleted }) {
  const color = STEP_COLORS[step.agent] || "#8B5CF6";
  const isDone = step.status === "done";
  const isRunning = step.status === "running";
  const isError = (step.errors || []).length > 0;

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1, duration: 0.4 }}
      className={`flex items-start gap-4 p-4 rounded-2xl transition-all duration-300 ${
        isRunning ? "glass" : isDone ? "glass" : "opacity-40"
      }`}
      style={{
        borderColor: isRunning ? `${color}40` : isDone ? `${color}25` : undefined,
        border: isRunning ? `1px solid ${color}40` : isDone ? `1px solid ${color}25` : "1px solid transparent",
        boxShadow: isRunning ? `0 0 20px ${color}15 inset` : undefined,
      }}
    >
      {/* Status icon */}
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5"
        style={{
          background: isDone ? `${color}20` : isRunning ? `${color}15` : "rgba(255,255,255,0.04)",
          border: `1px solid ${isDone ? color + "40" : isRunning ? color + "30" : "rgba(255,255,255,0.08)"}`,
        }}
      >
        {isDone ? (
          <CheckCircle2 size={18} style={{ color }} />
        ) : isRunning ? (
          <Loader2 size={18} style={{ color }} className="animate-spin" />
        ) : (
          <Clock size={16} className="text-slate-600" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5 flex-wrap">
          <span className="text-lg">{step.icon}</span>
          <span className={`font-semibold text-sm ${isDone || isRunning ? "text-white" : "text-slate-600"}`}>
            {step.label}
          </span>
          {isRunning && (
            <motion.span
              animate={{ opacity: [1, 0.3, 1] }}
              transition={{ repeat: Infinity, duration: 1.4 }}
              className="text-xs font-medium px-2 py-0.5 rounded-full"
              style={{ background: `${color}20`, color }}
            >
              Running
            </motion.span>
          )}
          {isDone && !isError && (
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 border border-green-500/20">
              Done
            </span>
          )}
        </div>

        <p className={`text-xs ${isDone || isRunning ? "text-slate-400" : "text-slate-700"}`}>
          {step.detail}
        </p>

        {/* Summary after done */}
        {isDone && step.summary && Object.keys(step.summary).length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="mt-2 flex flex-wrap gap-2"
          >
            {Object.entries(step.summary).map(([k, v]) => (
              v != null && (
                <span key={k} className="text-xs font-mono px-2 py-0.5 rounded-lg bg-white/5 text-slate-300 border border-white/10">
                  {k.replace(/_/g, " ")}: <span style={{ color }}>{String(v)}</span>
                </span>
              )
            ))}
          </motion.div>
        )}

        {/* Errors */}
        {isError && step.errors.map((e, i) => (
          <div key={i} className="mt-2 flex items-start gap-1.5 text-xs text-red-400">
            <AlertCircle size={12} className="mt-0.5 flex-shrink-0" />
            <span>{e}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

export default function AnalysisProgress() {
  const { steps, progress } = useFinancialStore();
  const stepCount = AGENT_ORDER.length;
  const doneCount = steps.filter((s) => s.status === "done").length;
  const currentStep = steps.find((s) => s.status === "running");

  // Merge ordered steps with received steps
  const ordered = AGENT_ORDER.map((agent) => {
    const found = steps.find((s) => s.agent === agent);
    return found || { agent, icon: "⏳", label: agent.replace(/_/g, " "), detail: "Waiting...", status: "pending" };
  });

  return (
    <div className="w-full flex flex-col gap-6">
      {/* Overall progress */}
      <div className="glass rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-white font-semibold">Analyzing your finances</h3>
            <p className="text-slate-400 text-sm mt-0.5">
              {currentStep ? currentStep.label : doneCount === stepCount ? "Analysis complete!" : "Starting..."}
            </p>
          </div>
          <div className="text-right">
            <span className="gradient-text text-3xl font-bold font-mono">{Math.round(progress)}</span>
            <span className="text-slate-400 text-lg font-mono">%</span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>

        {/* Step indicators */}
        <div className="flex items-center gap-1 mt-4">
          {AGENT_ORDER.map((agent, i) => {
            const s = steps.find((x) => x.agent === agent);
            const done = s?.status === "done";
            const running = s?.status === "running";
            const color = STEP_COLORS[agent];
            return (
              <div key={agent} className="flex items-center gap-1 flex-1">
                <div
                  className="h-1.5 flex-1 rounded-full transition-all duration-500"
                  style={{
                    background: done ? color : running ? `${color}60` : "rgba(255,255,255,0.08)",
                  }}
                />
                {i < AGENT_ORDER.length - 1 && (
                  <div className="w-1 h-1 rounded-full bg-white/10" />
                )}
              </div>
            );
          })}
        </div>
        <div className="flex justify-between mt-2">
          <span className="text-slate-600 text-xs">{doneCount}/{stepCount} agents complete</span>
          <span className="text-slate-600 text-xs font-mono">{Math.round(progress)}%</span>
        </div>
      </div>

      {/* Step list */}
      <div className="flex flex-col gap-3">
        <AnimatePresence>
          {ordered.map((step, i) => (
            <StepItem key={step.agent} step={step} index={i} totalCompleted={doneCount} />
          ))}
        </AnimatePresence>
      </div>

      {/* Floating GIF-like animation */}
      <div className="flex justify-center">
        <div className="relative w-24 h-24">
          {/* Pulsing rings */}
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="absolute inset-0 rounded-full border border-accent-purple/30"
              animate={{ scale: [1, 1.8 + i * 0.3], opacity: [0.6, 0] }}
              transition={{ repeat: Infinity, duration: 2, delay: i * 0.6, ease: "easeOut" }}
            />
          ))}
          <div className="absolute inset-0 flex items-center justify-center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
              className="w-16 h-16 rounded-2xl"
              style={{
                background: "linear-gradient(135deg, rgba(139,92,246,0.3), rgba(59,130,246,0.2))",
                border: "1px solid rgba(139,92,246,0.4)",
                boxShadow: "0 0 30px rgba(139,92,246,0.3)",
              }}
            />
          </div>
          <div className="absolute inset-0 flex items-center justify-center text-2xl">
            {currentStep?.icon || "🧠"}
          </div>
        </div>
      </div>
    </div>
  );
}
