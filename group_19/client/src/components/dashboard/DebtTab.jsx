import { motion } from "framer-motion";
import { fmt } from "../../utils/formatters.js";
import { CreditCard, TrendingDown, AlertTriangle, CheckCircle2 } from "lucide-react";

export default function DebtTab({ debt }) {
  if (!debt) return <div className="text-center py-12 text-slate-500">No debt data.</div>;

  const { has_debt, debt_signals = [], strategy, monthly_paydown_target, timeline_months, action_steps = [], warnings = [] } = debt;

  const strategyInfo = {
    avalanche: { label: "Avalanche", desc: "Highest APR first — mathematically optimal", color: "#EF4444" },
    snowball:  { label: "Snowball",  desc: "Smallest balance first — psychological wins",  color: "#F59E0B" },
    hybrid:    { label: "Hybrid",    desc: "Mix of avalanche & snowball approaches",        color: "#8B5CF6" },
  }[strategy] || { label: strategy, desc: "", color: "#8B5CF6" };

  if (!has_debt) {
    return (
      <div className="flex flex-col items-center gap-4 py-12">
        <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
          style={{ background: "rgba(16,185,129,0.15)", border: "1px solid rgba(16,185,129,0.3)" }}
        >
          <CheckCircle2 size={28} className="text-green-400" />
        </div>
        <div className="text-center">
          <p className="text-white font-semibold">No significant debt detected</p>
          <p className="text-slate-400 text-sm mt-1">Keep it up! Focus on building savings.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Strategy card */}
      <div className="glass rounded-2xl p-5"
        style={{ border: `1px solid ${strategyInfo.color}30` }}
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: `${strategyInfo.color}18`, border: `1px solid ${strategyInfo.color}35` }}
          >
            <CreditCard size={18} style={{ color: strategyInfo.color }} />
          </div>
          <div>
            <p className="text-white font-semibold">
              Recommended: <span style={{ color: strategyInfo.color }}>{strategyInfo.label} Strategy</span>
            </p>
            <p className="text-slate-400 text-xs mt-0.5">{strategyInfo.desc}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {[
            { label: "Monthly Paydown", value: fmt.currency(monthly_paydown_target), color: strategyInfo.color },
            { label: "Timeline", value: timeline_months ? `${timeline_months} months` : "—", color: "#06B6D4" },
          ].map((m) => (
            <div key={m.label} className="bg-white/[0.03] rounded-xl p-3">
              <p className="text-slate-500 text-xs mb-1">{m.label}</p>
              <p className="font-mono font-bold" style={{ color: m.color }}>{m.value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Debt signals */}
      {debt_signals.length > 0 && (
        <div>
          <p className="text-slate-400 text-xs uppercase tracking-wider font-medium mb-3">Detected Debts</p>
          <div className="flex flex-col gap-2">
            {debt_signals.map((d, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.06 }}
                className="flex items-center gap-3 p-3 glass rounded-xl"
              >
                <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm flex-shrink-0"
                  style={{ background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.25)" }}
                >
                  💳
                </div>
                <div className="flex-1">
                  <span className="text-white text-sm">{d.type || "Debt"}</span>
                  {d.description && <p className="text-slate-400 text-xs">{d.description}</p>}
                </div>
                {d.amount && <span className="font-mono text-red-400 font-semibold text-sm">{fmt.currency(d.amount)}</span>}
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Action steps */}
      {action_steps.length > 0 && (
        <div>
          <p className="text-slate-400 text-xs uppercase tracking-wider font-medium mb-3">Action Steps</p>
          <div className="flex flex-col gap-2">
            {action_steps.map((step, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-xl"
                style={{ background: "rgba(59,130,246,0.06)", border: "1px solid rgba(59,130,246,0.15)" }}
              >
                <span className="w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5"
                  style={{ background: "rgba(59,130,246,0.2)", color: "#93C5FD" }}
                >
                  {i + 1}
                </span>
                <span className="text-slate-300 text-sm">{step}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Warnings */}
      {warnings.length > 0 && (
        <div>
          <p className="text-slate-400 text-xs uppercase tracking-wider font-medium mb-3">Cautions</p>
          {warnings.map((w, i) => (
            <div key={i} className="flex items-start gap-2 p-3 rounded-xl bg-yellow-500/6 border border-yellow-500/15 mb-2">
              <AlertTriangle size={14} className="text-yellow-400 mt-0.5 flex-shrink-0" />
              <span className="text-slate-300 text-sm">{w}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
