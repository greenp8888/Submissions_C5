import { motion } from "framer-motion";
import { fmt } from "../../utils/formatters.js";
import { Shield, Target, Zap, Building2, ExternalLink } from "lucide-react";

export default function SavingsTab({ savings }) {
  if (!savings) return <div className="text-center py-12 text-slate-500">No savings data.</div>;

  const { emergency_fund, savings_goals = [], quick_wins = [], account_suggestions = [], bank_offers = [], recommended_rate } = savings;

  return (
    <div className="flex flex-col gap-6">
      {/* Emergency Fund */}
      {emergency_fund && (
        <div className="glass rounded-2xl p-5"
          style={{ border: "1px solid rgba(16,185,129,0.25)" }}
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: "rgba(16,185,129,0.15)", border: "1px solid rgba(16,185,129,0.3)" }}
            >
              <Shield size={18} className="text-green-400" />
            </div>
            <div>
              <p className="text-white font-semibold">Emergency Fund</p>
              <p className="text-slate-400 text-xs">3–6 months of expenses</p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
            {[
              { label: "Target", value: fmt.currency(emergency_fund.target_amount), color: "#10B981" },
              { label: "Monthly Contribution", value: fmt.currency(emergency_fund.monthly_contribution), color: "#06B6D4" },
              { label: "Timeline", value: emergency_fund.months_to_target ? `${emergency_fund.months_to_target} mo` : "—", color: "#F59E0B" },
            ].map((m) => (
              <div key={m.label} className="bg-white/[0.03] rounded-xl p-3">
                <p className="text-slate-500 text-xs mb-1">{m.label}</p>
                <p className="font-mono font-bold" style={{ color: m.color }}>{m.value}</p>
              </div>
            ))}
          </div>

          {/* Progress bar toward target */}
          {emergency_fund.current_amount != null && (
            <div>
              <div className="flex justify-between text-xs text-slate-500 mb-1.5">
                <span>Current: {fmt.currency(emergency_fund.current_amount)}</span>
                <span>{((emergency_fund.current_amount / emergency_fund.target_amount) * 100).toFixed(0)}%</span>
              </div>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{
                    width: `${Math.min(100, (emergency_fund.current_amount / emergency_fund.target_amount) * 100)}%`,
                    background: "linear-gradient(90deg,#10B981,#06B6D4)",
                  }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Savings Goals */}
      {savings_goals.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Target size={16} className="text-accent-purple" />
            <p className="text-white font-semibold text-sm">Savings Goals</p>
            {recommended_rate && (
              <span className="ml-auto text-xs font-mono text-accent-cyan">Target rate: {fmt.pct(recommended_rate)}</span>
            )}
          </div>
          <div className="flex flex-col gap-3">
            {savings_goals.map((goal, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                className="glass rounded-xl p-4 flex items-start gap-3"
              >
                <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm flex-shrink-0"
                  style={{ background: "rgba(139,92,246,0.15)", border: "1px solid rgba(139,92,246,0.25)" }}
                >
                  🎯
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-white font-medium text-sm">{goal.label || goal.goal}</span>
                    {(goal.timeline_months || goal.timeframe) && (
                      <span className="text-xs text-accent-cyan font-mono">
                        {goal.timeline_months ? `${goal.timeline_months} mo` : goal.timeframe}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs font-mono">
                    <span className="text-green-400">{fmt.currency(goal.target_amount)}</span>
                    {(goal.monthly_contribution || goal.monthly_savings) && (
                      <span className="text-slate-500">→ {fmt.currency(goal.monthly_contribution || goal.monthly_savings)}/mo</span>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Wins */}
      {quick_wins.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Zap size={16} className="text-yellow-400" />
            <p className="text-white font-semibold text-sm">Quick Wins</p>
          </div>
          <div className="flex flex-col gap-2">
            {quick_wins.map((tip, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-yellow-500/6 border border-yellow-500/15">
                <span className="text-yellow-400 text-xs font-bold mt-0.5 flex-shrink-0">#{i + 1}</span>
                <span className="text-slate-300 text-sm">{tip}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Account suggestions */}
      {account_suggestions.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Building2 size={16} className="text-accent-blue" />
            <p className="text-white font-semibold text-sm">Recommended Accounts</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {account_suggestions.map((a, i) => (
              <span key={i} className="text-xs px-3 py-1.5 rounded-xl glass text-slate-300 border border-white/10">
                {a}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Bank Offers */}
      {bank_offers.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <ExternalLink size={16} className="text-accent-cyan" />
            <p className="text-white font-semibold text-sm">Live Bank Offers</p>
            <span className="text-xs text-accent-cyan bg-accent-cyan/10 px-2 py-0.5 rounded-full border border-accent-cyan/20">
              via Tavily
            </span>
          </div>
          <div className="flex flex-col gap-2">
            {bank_offers.map((offer, i) => (
              <a
                key={i}
                href={offer.url}
                target="_blank"
                rel="noopener noreferrer"
                className="glass glass-hover rounded-xl p-4 flex items-start gap-3 group"
              >
                <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ background: "rgba(6,182,212,0.15)", border: "1px solid rgba(6,182,212,0.25)" }}
                >
                  🏦
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-white text-sm font-medium group-hover:text-accent-cyan transition-colors truncate">{offer.title}</p>
                  {offer.snippet && <p className="text-slate-400 text-xs mt-0.5 line-clamp-2">{offer.snippet}</p>}
                </div>
                <ExternalLink size={12} className="text-slate-500 group-hover:text-accent-cyan transition-colors flex-shrink-0 mt-1" />
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
