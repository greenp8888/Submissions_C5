import { motion } from "framer-motion";
import { fmt } from "../../utils/formatters.js";
import { AlertCircle, TrendingDown, DollarSign } from "lucide-react";

function AllocRow({ alloc, index }) {
  const currentSpend = Math.abs(alloc.current_avg ?? alloc.current_spend ?? 0);
  const pct = Math.min(100, Math.abs(alloc.variance_pct || 0));
  const isOver = (alloc.variance_pct || 0) > 0;
  const color = isOver ? "#EF4444" : "#10B981";

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      className="flex flex-col gap-2 p-4 glass rounded-xl glass-hover"
    >
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full flex-shrink-0"
            style={{ background: isOver ? "#EF4444" : "#10B981" }} />
          <span className="text-white text-sm font-medium">{alloc.category}</span>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="text-slate-400">{fmt.currency(currentSpend)}</span>
          <span className="text-slate-600">→</span>
          <span className="text-white font-semibold">{fmt.currency(alloc.recommended)}</span>
          <span
            className="px-2 py-0.5 rounded-full font-semibold"
            style={{
              background: `${color}18`,
              color,
              border: `1px solid ${color}30`,
            }}
          >
            {isOver ? "+" : ""}{(alloc.variance_pct || 0).toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Mini progress bar showing current vs recommended */}
      <div className="flex items-center gap-2 text-xs">
        <div className="flex-1 h-1.5 rounded-full overflow-hidden bg-white/5">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${Math.min(100, (currentSpend / Math.max(alloc.recommended || 1, currentSpend || 1)) * 100)}%`,
              background: isOver
                ? "linear-gradient(90deg,#F59E0B,#EF4444)"
                : "linear-gradient(90deg,#10B981,#06B6D4)",
            }}
          />
        </div>
        {alloc.note && <span className="text-slate-600 truncate max-w-xs">{alloc.note}</span>}
      </div>
    </motion.div>
  );
}

export default function BudgetTab({ budget }) {
  if (!budget) return <div className="text-center py-12 text-slate-500">No budget data.</div>;

  const { allocations = [], alerts = [], surplus, total_budgeted, monthly_summary } = budget;

  return (
    <div className="flex flex-col gap-6">
      {/* Summary strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {[
          { label: "Total Budgeted", value: fmt.currency(total_budgeted), color: "#8B5CF6" },
          { label: "Monthly Surplus", value: fmt.currency(surplus), color: surplus >= 0 ? "#10B981" : "#EF4444" },
          { label: "Categories", value: allocations.length, color: "#3B82F6" },
        ].map((m) => (
          <div key={m.label} className="glass rounded-xl p-4">
            <p className="text-slate-400 text-xs mb-1">{m.label}</p>
            <p className="font-mono font-bold text-lg" style={{ color: m.color }}>{m.value}</p>
          </div>
        ))}
      </div>

      {/* Summary text */}
      {monthly_summary && (
        <div className="glass rounded-xl p-4 flex items-start gap-3">
          <DollarSign size={16} className="text-accent-purple mt-0.5 flex-shrink-0" />
          <p className="text-slate-300 text-sm leading-relaxed">{monthly_summary}</p>
        </div>
      )}

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="text-slate-400 text-xs uppercase tracking-wider font-medium">Alerts</p>
          {alerts.map((a, i) => {
            const text   = typeof a === "string" ? a : (a.message || a.category || JSON.stringify(a));
            const cat    = typeof a === "object" && a.category ? a.category : null;
            const atype  = typeof a === "object" && a.type     ? a.type     : null;
            return (
              <div key={i} className="flex items-start gap-2 p-3 rounded-xl bg-yellow-500/8 border border-yellow-500/20">
                <AlertCircle size={14} className="text-yellow-400 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  {(cat || atype) && (
                    <div className="flex items-center gap-1.5 mb-0.5">
                      {cat   && <span className="text-yellow-300 text-[10px] font-semibold">{cat}</span>}
                      {atype && <span className="text-[9px] px-1.5 py-0.5 rounded font-mono text-yellow-500 bg-yellow-500/10">{atype}</span>}
                    </div>
                  )}
                  <span className="text-yellow-200 text-sm">{text}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Allocations */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between mb-1">
          <p className="text-slate-400 text-xs uppercase tracking-wider font-medium">Category Allocations</p>
          <div className="flex items-center gap-3 text-xs text-slate-600">
            <span>Current → Recommended</span>
          </div>
        </div>
        {allocations.map((a, i) => <AllocRow key={i} alloc={a} index={i} />)}
      </div>
    </div>
  );
}
