import { useAnimatedCounter } from "../../hooks/useAnimatedCounter.js";
import { motion } from "framer-motion";

export default function MetricCard({ icon, label, value, rawValue, delta, deltaLabel, color = "#8B5CF6", delay = 0 }) {
  const animated = useAnimatedCounter(rawValue, 1000);

  const displayValue = rawValue != null
    ? (typeof value === "function" ? value(animated) : value)
    : value;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="glass glass-hover rounded-2xl p-5 flex flex-col gap-3"
      style={{ borderColor: `${color}22` }}
    >
      {/* Icon + label */}
      <div className="flex items-center gap-3">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center text-lg flex-shrink-0"
          style={{ background: `${color}18`, border: `1px solid ${color}30` }}
        >
          {icon}
        </div>
        <span className="text-slate-400 text-sm font-medium">{label}</span>
      </div>

      {/* Value */}
      <div className="flex items-end justify-between gap-2">
        <span
          className="font-mono font-bold text-2xl leading-none"
          style={{ color }}
        >
          {displayValue ?? "—"}
        </span>
        {delta != null && (
          <span
            className={`text-xs font-semibold px-2 py-1 rounded-lg mb-0.5 ${
              delta >= 0
                ? "bg-green-500/10 text-green-400 border border-green-500/20"
                : "bg-red-500/10 text-red-400 border border-red-500/20"
            }`}
          >
            {delta >= 0 ? "+" : ""}{delta?.toFixed(1)}{deltaLabel || "%"}
          </span>
        )}
      </div>
    </motion.div>
  );
}
