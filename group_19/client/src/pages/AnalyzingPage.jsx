import { useEffect } from "react";
import { motion } from "framer-motion";
import { AlertCircle, ArrowLeft } from "lucide-react";
import AnalysisProgress from "../components/analysis/AnalysisProgress.jsx";
import { useFinancialStore } from "../store/financialStore.js";

export default function AnalyzingPage() {
  const { analysisError, setPage, progress } = useFinancialStore();

  return (
    <div className="min-h-screen px-4 py-8 max-w-2xl mx-auto">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-3 mb-8"
      >
        <button
          onClick={() => setPage("upload")}
          className="w-8 h-8 rounded-lg glass glass-hover flex items-center justify-center text-slate-400"
        >
          <ArrowLeft size={14} />
        </button>
        <div>
          <h2 className="text-white font-bold text-lg">FinanceIQ Analysis</h2>
          <p className="text-slate-500 text-xs">Multi-agent AI pipeline running</p>
        </div>
      </motion.div>

      {/* Error state */}
      {analysisError && (
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mb-6 p-4 rounded-2xl bg-red-500/10 border border-red-500/30 flex items-start gap-3"
        >
          <AlertCircle size={18} className="text-red-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-red-300 font-semibold text-sm">Analysis Error</p>
            <p className="text-red-400/70 text-xs mt-1">{analysisError}</p>
            <button
              onClick={() => setPage("upload")}
              className="mt-2 text-xs text-red-400 hover:text-red-300 underline"
            >
              Go back and retry
            </button>
          </div>
        </motion.div>
      )}

      {/* Progress display */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <AnalysisProgress />
      </motion.div>

      {/* Tip box */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="mt-8 glass rounded-2xl p-4 text-center"
      >
        <p className="text-slate-500 text-xs">
          💡 <span className="text-slate-400">Each AI agent specializes in one domain</span> — together they deliver
          bank-grade financial intelligence in seconds.
        </p>
      </motion.div>
    </div>
  );
}
