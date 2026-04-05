import { useCallback, useRef } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Sparkles, TrendingUp, Shield, Zap } from "lucide-react";
import HeroScene from "../components/three/HeroScene.jsx";
import FileDropzone from "../components/upload/FileDropzone.jsx";
import ConfigPanel from "../components/upload/ConfigPanel.jsx";
import { useFinancialStore, AGENT_ORDER } from "../store/financialStore.js";

const FEATURES = [
  { icon: "🧠", label: "6 Specialized AI Agents" },
  { icon: "📊", label: "Deep Expense Analysis" },
  { icon: "💳", label: "Debt Payoff Strategy" },
  { icon: "🏦", label: "Live Bank Rate Search" },
  { icon: "🎯", label: "Personalized Goals" },
  { icon: "📋", label: "Full Financial Report" },
];

export default function UploadPage() {
  const { file, config, setPage, resetAnalysis, addStep, updateStep, setProgress, setResult, setAnalysisError } = useFinancialStore();
  const abortRef = useRef(null);

  const canAnalyze = !!file && !!config.openrouterKey;

  const handleAnalyze = useCallback(async () => {
    if (!canAnalyze) return;

    resetAnalysis();
    setPage("analyzing");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("openrouterKey", config.openrouterKey);
    formData.append("tavilyKey", config.tavilyKey || "");
    formData.append("model", config.model);
    formData.append("goals", config.goals);

    try {
      const res = await fetch("/api/analyze", { method: "POST", body: formData });
      if (!res.ok) throw new Error("Server error");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let stepsDone = 0;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          const trimmed = line.replace(/^data:\s*/, "").trim();
          if (!trimmed) continue;
          try {
            const event = JSON.parse(trimmed);

            if (event.type === "step_start") {
              addStep({ ...event, status: "running" });
            } else if (event.type === "step_done") {
              stepsDone++;
              updateStep(event.agent, { status: "done", summary: event.summary, errors: event.errors || [] });
              setProgress(Math.round((stepsDone / AGENT_ORDER.length) * 100));
            } else if (event.type === "done") {
              setProgress(100);
              setResult(event.result);
              setTimeout(() => setPage("dashboard"), 800);
            } else if (event.type === "error") {
              setAnalysisError(event.message);
            }
          } catch {}
        }
      }
    } catch (err) {
      setAnalysisError(err.message);
    }
  }, [file, config, canAnalyze, resetAnalysis, setPage, addStep, updateStep, setProgress, setResult, setAnalysisError]);

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <div className="relative overflow-hidden" style={{ minHeight: "45vh" }}>
        <HeroScene />

        {/* Orbs */}
        <div className="orb orb-purple w-96 h-96 -top-32 -left-32 opacity-50" />
        <div className="orb orb-cyan w-64 h-64 top-10 right-10 opacity-30" />

        <div className="relative z-10 flex flex-col items-center justify-center h-full px-6 py-16 text-center">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-2 mb-6 px-4 py-1.5 rounded-full glass text-xs font-medium text-slate-300"
            style={{ border: "1px solid rgba(139,92,246,0.35)" }}
          >
            <Sparkles size={12} className="text-accent-purple" />
            AI-Powered · Multi-Agent · Real-Time Analysis
          </motion.div>

          {/* Heading */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="text-4xl sm:text-6xl font-black leading-tight mb-4"
          >
            Your Elite{" "}
            <span className="gradient-text">Financial</span>
            <br />
            Coach
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.6 }}
            className="text-slate-400 text-lg max-w-xl mb-8"
          >
            Upload your transactions. Six AI specialists analyze your finances
            and deliver a personalized wealth-building blueprint.
          </motion.p>

          {/* Feature pills */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.35 }}
            className="flex flex-wrap gap-2 justify-center"
          >
            {FEATURES.map((f) => (
              <span key={f.label}
                className="text-xs px-3 py-1.5 rounded-full glass text-slate-400 border border-white/8"
              >
                {f.icon} {f.label}
              </span>
            ))}
          </motion.div>
        </div>
      </div>

      {/* ── Main form ───────────────────────────────────────────────────── */}
      <div className="flex-1 px-4 pb-16 -mt-6 max-w-2xl mx-auto w-full">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="flex flex-col gap-4"
        >
          {/* File upload */}
          <div className="glass rounded-2xl p-5">
            <p className="text-slate-400 text-xs uppercase tracking-wider font-medium mb-3">
              Step 1 · Upload Transactions
            </p>
            <FileDropzone />
          </div>

          {/* Config */}
          <ConfigPanel />

          {/* Analyze button */}
          <motion.button
            whileHover={canAnalyze ? { scale: 1.02 } : {}}
            whileTap={canAnalyze ? { scale: 0.98 } : {}}
            onClick={handleAnalyze}
            disabled={!canAnalyze}
            className="btn-primary flex items-center justify-center gap-3 py-4 text-base rounded-2xl"
          >
            {canAnalyze ? (
              <>
                <Sparkles size={18} />
                Analyze My Finances
                <ArrowRight size={18} />
              </>
            ) : (
              <>
                <Shield size={18} />
                {!file ? "Upload a file first" : "Enter OpenRouter API key"}
              </>
            )}
          </motion.button>

          {/* Sample file hint */}
          <p className="text-center text-slate-600 text-xs">
            Try with the sample file in{" "}
            <span className="font-mono text-slate-500">data/transactions_dummy.csv</span>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
