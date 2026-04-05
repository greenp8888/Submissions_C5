import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard, Lightbulb, PieChart,
  PiggyBank, CreditCard, FileText, RefreshCw,
} from "lucide-react";
import { useFinancialStore } from "../store/financialStore.js";
import { fmt, scoreLabel } from "../utils/formatters.js";
import MetricCard from "../components/ui/MetricCard.jsx";
import HealthScoreRing from "../components/ui/HealthScoreRing.jsx";
import InsightsTab from "../components/dashboard/InsightsTab.jsx";
import BudgetTab from "../components/dashboard/BudgetTab.jsx";
import SavingsTab from "../components/dashboard/SavingsTab.jsx";
import DebtTab from "../components/dashboard/DebtTab.jsx";
import ChartsTab from "../components/dashboard/ChartsTab.jsx";
import ReportTab from "../components/dashboard/ReportTab.jsx";

const TABS = [
  { id: "insights", label: "Insights",  Icon: Lightbulb },
  { id: "budget",   label: "Budget",    Icon: LayoutDashboard },
  { id: "savings",  label: "Savings",   Icon: PiggyBank },
  { id: "debt",     label: "Debt",      Icon: CreditCard },
  { id: "charts",   label: "Charts",    Icon: PieChart },
  { id: "report",   label: "Report",    Icon: FileText },
];

export default function DashboardPage() {
  const { result, setPage, resetChat } = useFinancialStore();
  const [activeTab, setActiveTab] = useState("insights");

  if (!result) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-400 mb-4">No analysis result available.</p>
          <button onClick={() => setPage("chat")} className="btn-primary">
            Start Analysis
          </button>
        </div>
      </div>
    );
  }

  const snap = result.financial_snapshot || {};
  const score = result.health_score;
  const { color: scoreColor } = scoreLabel(score || 0);

  const metrics = [
    {
      icon: "💰",
      label: "Total Income",
      value: fmt.currency(snap.total_income),
      rawValue: snap.total_income,
      color: "#10B981",
    },
    {
      icon: "💸",
      label: "Net Expenses",
      value: fmt.currency(snap.total_expenses),
      rawValue: snap.total_expenses,
      color: "#EF4444",
    },
    {
      icon: "📈",
      label: "Savings Rate",
      value: fmt.pct(snap.savings_rate),
      rawValue: snap.savings_rate,
      color: snap.savings_rate > 20 ? "#10B981" : snap.savings_rate > 0 ? "#F59E0B" : "#EF4444",
    },
    {
      icon: "🏦",
      label: "Net Savings",
      value: fmt.currency(snap.net_savings),
      rawValue: snap.net_savings,
      color: (snap.net_savings || 0) >= 0 ? "#8B5CF6" : "#EF4444",
    },
  ];

  return (
    <div className="min-h-screen pb-16">
      {/* ── Top nav ──────────────────────────────────────────────────────── */}
      <div className="sticky top-0 z-30 glass border-b border-white/5 px-4 py-3">
        <div className="max-w-5xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="text-white font-semibold text-sm">Dashboard</span>
            <span className="text-slate-600 text-xs">· Analysis Results</span>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl glass text-xs font-mono whitespace-nowrap">
              <div className="dot-active" />
              <span className="text-slate-300">Score: </span>
              <span className="font-bold" style={{ color: scoreColor }}>{Math.round(score || 0)}/100</span>
            </div>
            <button
              onClick={() => { resetChat(); setPage("chat"); }}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl glass glass-hover text-slate-400 text-xs"
            >
              <RefreshCw size={12} />
              New Analysis
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 pt-6">
        {/* ── Health Hero ────────────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          {/* Full-width score card */}
          <div
            className="glass rounded-2xl p-8 mb-4 flex flex-col items-center gap-4 relative overflow-hidden"
            style={{ border: `1px solid ${scoreColor}25` }}
          >
            {/* Radial glow backdrop */}
            <div
              className="absolute inset-0 pointer-events-none"
              style={{
                background: `radial-gradient(ellipse 60% 80% at 50% 50%, ${scoreColor}12 0%, transparent 70%)`,
              }}
            />
            {/* Top label */}
            <p className="text-slate-400 text-xs uppercase tracking-widest font-semibold z-10 flex items-center gap-2">
              <span
                className="inline-block w-1.5 h-1.5 rounded-full"
                style={{ background: scoreColor, boxShadow: `0 0 6px ${scoreColor}` }}
              />
              Financial Health Score
            </p>

            {/* Ring */}
            <div className="z-10">
              <HealthScoreRing score={score} size={196} />
            </div>

            {/* Transaction count pill */}
            <div
              className="z-10 flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
                color: "#94a3b8",
              }}
            >
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              {snap.transaction_count || 0} transactions analyzed
            </div>
          </div>

          {/* Metric cards — responsive 2→4 col */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {metrics.map((m, i) => (
              <MetricCard key={m.label} {...m} delay={i * 0.08} />
            ))}
          </div>
        </motion.div>

        {/* ── Errors ──────────────────────────────────────────────────────── */}
        {(result.errors || []).length > 0 && (
          <div className="mb-5 p-4 rounded-2xl bg-yellow-500/8 border border-yellow-500/20">
            <p className="text-yellow-400 text-xs font-medium mb-2">⚠ Some agents reported issues:</p>
            {result.errors.map((e, i) => (
              <p key={i} className="text-yellow-300/70 text-xs">{e}</p>
            ))}
          </div>
        )}

        {/* ── Tab navigation ───────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex items-center gap-1 glass rounded-2xl p-1.5 mb-5 overflow-x-auto"
        >
          {TABS.map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`tab-btn flex items-center gap-1.5 flex-shrink-0 ${activeTab === id ? "active" : ""}`}
            >
              <Icon size={13} />
              {label}
            </button>
          ))}
        </motion.div>

        {/* ── Tab content ──────────────────────────────────────────────── */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}
          >
            {activeTab === "insights" && (
              <InsightsTab insights={result.financial_insights || []} />
            )}
            {activeTab === "budget" && (
              <BudgetTab budget={result.budget_recommendations} />
            )}
            {activeTab === "savings" && (
              <SavingsTab savings={result.savings_plan} />
            )}
            {activeTab === "debt" && (
              <DebtTab debt={result.debt_plan} />
            )}
            {activeTab === "charts" && (
              <ChartsTab snapshot={snap} budget={result.budget_recommendations} />
            )}
            {activeTab === "report" && (
              <ReportTab report={result.final_report} result={result} />
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
