import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, AlertTriangle, Info, Lightbulb } from "lucide-react";
import { severityColor } from "../../utils/formatters.js";

const ICONS = {
  critical: <AlertTriangle size={16} />,
  warning:  <AlertTriangle size={16} />,
  positive: <TrendingUp size={16} />,
  info:     <Info size={16} />,
};

export default function InsightsTab({ insights = [] }) {
  if (!insights.length) return (
    <div className="text-center py-12 text-slate-500">No insights available.</div>
  );

  const sorted = [...insights].sort((a, b) => {
    const order = { critical: 0, warning: 1, positive: 2, info: 3 };
    return (order[a.severity] ?? 3) - (order[b.severity] ?? 3);
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-3 mb-2">
        <Lightbulb size={18} className="text-accent-purple" />
        <h3 className="text-white font-semibold">Key Financial Insights</h3>
        <span className="text-xs text-slate-500 font-mono">{insights.length} findings</span>
      </div>

      {sorted.map((insight, i) => {
        const { bg, border, text, badge } = severityColor(insight.severity);
        return (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.07, duration: 0.4 }}
            className="rounded-2xl p-5 flex flex-col gap-3"
            style={{ background: bg, border: `1px solid ${border}` }}
          >
            <div className="flex items-start gap-3">
              <div className="mt-0.5 flex-shrink-0" style={{ color: text }}>
                {ICONS[insight.severity] || ICONS.info}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span className="font-semibold text-white text-sm">{insight.category || insight.finding?.slice(0, 60)}</span>
                  <span className={badge}>{insight.severity || "info"}</span>
                </div>
                <p className="text-slate-300 text-sm leading-relaxed">{insight.finding}</p>
              </div>
            </div>
            {insight.recommendation && (
              <div className="flex items-start gap-2 pl-7">
                <div className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0" style={{ background: text }} />
                <p className="text-slate-400 text-xs leading-relaxed">{insight.recommendation}</p>
              </div>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}
