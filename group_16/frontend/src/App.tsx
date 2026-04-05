import { useState, useRef, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { parseMultipleStatements } from "./lib/csv_parser";
import { 
  buildPrompt, 
  DEBT_ANALYZER_PROMPT, 
  BUDGET_COACH_PROMPT, 
  SAVINGS_PLANNER_PROMPT, 
  PAYOFF_OPTIMIZER_PROMPT 
} from "./lib/agent_prompts";

// ── Palette ──
const COLORS = ["#8a7df7", "#28b88d", "#ea6565", "#499eec", "#eab45c", "#d4537e", "#639922", "#888780", "#e24b4a"];
const fmt = (n: number) => "$" + Number(n).toLocaleString("en-US", { maximumFractionDigits: 0 });
const fmtK = (n: number) => n >= 1000 ? "$" + (n / 1000).toFixed(1) + "k" : fmt(n);

// ── UI Components ──
function StatCard({ label, value, sub, accent }: any) {
  return (
    <div className="stat-card glass-panel">
      <div style={{ fontSize: 13, color: "var(--color-text-secondary)", marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 600, color: accent || "var(--color-text-primary)" }}>{value}</div>
      {sub && <div style={{ fontSize: 12, color: "var(--color-text-tertiary)", marginTop: 6 }}>{sub}</div>}
    </div>
  );
}

function SectionHeader({ title }: { title: string }) {
  return <div style={{ fontSize: 15, fontWeight: 600, color: "var(--color-text-primary)", margin: "32px 0 16px" }}>{title}</div>;
}

function Flag({ text, color }: any) {
  return <div className={`flag ${color || ''}`}>{text}</div>;
}

// ── OVERVIEW TAB ──
function OverviewTab({ fin }: any) {
  const sum = fin.summary;
  const cats = [
    { name: "Income", value: sum.total_income },
    { name: "Spend", value: sum.total_spend }
  ];

  return (
    <div className="animate-fade-in">
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 24 }}>
        <StatCard label="Avg monthly income" value={fmt(sum.avg_monthly_income)} sub={`${sum.months_analyzed} months analyzed`} />
        <StatCard label="Avg monthly surplus" value={fmt(sum.avg_monthly_surplus)} accent="var(--color-success)" sub="available to save or pay debt" />
        <StatCard label="Total Spent" value={fmt(sum.total_spend)} accent="var(--color-danger)" />
      </div>

      <div style={{ display: "flex", gap: 20 }}>
        <div className="glass-panel" style={{ flex: 1, padding: 24 }}>
          <SectionHeader title="Income vs Spend Breakdown" />
          <div style={{ height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={cats} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} innerRadius={60} paddingAngle={2}>
                  <Cell fill="var(--color-brand-primary)" />
                  <Cell fill="var(--color-danger)" />
                </Pie>
                <Tooltip formatter={(v: number) => fmt(v)} contentStyle={{ background: "var(--color-background-primary)", borderColor: "var(--color-border-primary)", borderRadius: 12, color: "#fff" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── DEBT TAB ──
function DebtTab({ agents }: any) {
  const { debt } = agents;
  if (!debt || !debt.accounts) return <div className="glass-panel p-4">No debt analysis available.</div>;

  return (
    <div className="animate-fade-in">
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 24 }}>
        <StatCard label="Estimated Total Debt" value={fmtK(debt.summary.estimated_total_balance)} accent="var(--color-danger)" />
        <StatCard label="Monthly Minimums" value={fmt(debt.summary.total_monthly_debt_payments)} />
        <StatCard label="Debt-to-Income (Mo)" value={(debt.summary.debt_to_income_ratio * 100).toFixed(1) + "%"} accent="var(--color-warning)" />
      </div>

      {debt.flags && debt.flags.map((f: string, i: number) => <Flag key={i} text={f} color="red" />)}

      <SectionHeader title="Debt Accounts" />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 16 }}>
        {debt.accounts.map((a: any, i: number) => (
          <div key={i} className="glass-panel" style={{ padding: "18px 20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <div style={{ fontSize: 15, fontWeight: 600, color: "var(--color-text-primary)" }}>{a.name}</div>
                <div style={{ fontSize: 13, color: "var(--color-text-tertiary)", marginTop: 4 }}>{a.type.replace("_", " ")} · {a.estimated_apr || "?"}% APR</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 18, fontWeight: 600, color: "var(--color-text-primary)" }}>{fmtK(a.estimated_balance)}</div>
                <div style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>{fmt(a.monthly_payment)}/mo</div>
              </div>
            </div>
            <div style={{ marginTop: 16, background: "var(--color-background-tertiary)", borderRadius: 8, height: 8, overflow: "hidden" }}>
              <div style={{ height: "100%", width: Math.min(100, (a.estimated_balance / debt.summary.estimated_total_balance) * 100) + "%", background: COLORS[i % COLORS.length], borderRadius: 8 }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── BUDGET TAB ──
function BudgetTab({ agents }: any) {
  const { budget } = agents;
  if (!budget) return <div className="glass-panel p-4">No budget analysis available.</div>;

  return (
    <div className="animate-fade-in">
      <SectionHeader title="Top Overspend Findings" />
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {budget.top_overspend_findings?.map((f: string, i: number) => <Flag key={i} text={f} color="amber" />)}
      </div>

      <SectionHeader title="Action Items" />
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {budget.action_items?.map((a: any, i: number) => (
          <div key={i} className="glass-panel" style={{ display: "flex", gap: 16, padding: "16px 20px" }}>
            <div style={{ width: 28, height: 28, borderRadius: "50%", background: "rgba(138, 125, 247, 0.15)", color: "var(--color-brand-primary)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 600, flexShrink: 0, marginTop: 2 }}>{a.priority}</div>
            <div>
              <div style={{ fontSize: 15, color: "var(--color-text-primary)", lineHeight: 1.5 }}>{a.action}</div>
              {a.estimated_monthly_saving && <div style={{ fontSize: 13, color: "var(--color-success)", marginTop: 6, fontWeight: 500 }}>Saves ~{fmt(a.estimated_monthly_saving)}/month</div>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── SAVINGS TAB ──
function SavingsTab({ agents }: any) {
  const { savings } = agents;
  if (!savings) return <div className="glass-panel p-4">No savings analysis available.</div>;

  return (
    <div className="animate-fade-in">
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 24 }}>
        <StatCard label="Current savings rate" value={savings.savings_assessment.current_savings_rate_pct + "%"} accent="var(--color-success)" />
        <StatCard label="Target save/month" value={fmt(savings.savings_assessment.recommended_monthly_savings)} />
        <StatCard label="Emergency fund gap" value={fmt(savings.emergency_fund.gap)} accent="var(--color-danger)" sub={savings.emergency_fund.months_to_fund_at_recommended_rate + " months to close"} />
      </div>

      <SectionHeader title="Emergency Fund Progress" />
      <div className="glass-panel" style={{ padding: "20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 14, marginBottom: 10 }}>
          <span style={{ color: "var(--color-text-secondary)" }}>Current: <strong style={{ color: "var(--color-text-primary)" }}>{fmt(savings.emergency_fund.estimated_current_amount)}</strong></span>
          <span style={{ color: "var(--color-text-secondary)" }}>Target: <strong style={{ color: "var(--color-text-primary)" }}>{fmt(savings.emergency_fund.target_amount)}</strong></span>
        </div>
        <div style={{ background: "var(--color-background-tertiary)", borderRadius: 10, height: 16, overflow: "hidden" }}>
          <div style={{ height: "100%", width: (savings.emergency_fund.estimated_current_amount / savings.emergency_fund.target_amount * 100) + "%", background: "linear-gradient(90deg, var(--color-brand-secondary), var(--color-brand-primary))", borderRadius: 10, transition: "width .5s" }} />
        </div>
      </div>

      <SectionHeader title="Priority Goals" />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 16 }}>
        {savings.goals?.map((g: any, i: number) => (
          <div key={i} className="glass-panel" style={{ padding: "18px 20px" }}>
            <div style={{ fontSize: 15, fontWeight: 600, color: "var(--color-text-primary)" }}>{g.name}</div>
            <div style={{ fontSize: 13, color: "var(--color-text-tertiary)", marginTop: 6, lineHeight: 1.5 }}>{g.rationale}</div>
            <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--color-border-secondary)", display: "flex", justifyContent: "space-between" }}>
              <div>
                <div style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>Target</div>
                <div style={{ fontSize: 16, fontWeight: 600 }}>{fmt(g.target_amount)}</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>Timeline</div>
                <div style={{ fontSize: 16, fontWeight: 600, color: "var(--color-brand-primary)" }}>{g.months_to_reach} mo</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── PAYOFF TAB ──
function PayoffTab({ agents }: any) {
  const { payoff } = agents;
  if (!payoff || !payoff.avalanche) return <div className="glass-panel p-4">No payoff analysis available.</div>;

  const [mode, setMode] = useState<"avalanche" | "snowball">("avalanche");
  const active = payoff[mode];

  return (
    <div className="animate-fade-in">
      <Flag text={"Recommendation: " + (payoff.comparison?.recommendation_rationale || "Go with Avalanche.")} color="info" />

      <div style={{ display: "flex", gap: 12, margin: "24px 0" }}>
        {["avalanche", "snowball"].map((s: any) => (
          <button key={s} onClick={() => setMode(s)} className={`btn-tab ${mode === s ? 'active' : ''}`} style={{ flex: 1, padding: "12px 0", fontSize: 15 }}>
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
        <StatCard label="Payoff Time" value={active.total_months_to_payoff + " mo"} />
        <StatCard label="Total Interest Paid" value={fmt(active.total_interest_paid)} accent={mode === "avalanche" ? "var(--color-success)" : "var(--color-warning)"} />
      </div>

      <SectionHeader title="Suggested Payoff Order" />
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {active.payoff_order?.map((name: string, i: number) => (
          <div key={i} className="glass-panel" style={{ display: "flex", alignItems: "center", gap: 16, padding: "12px 20px" }}>
            <div style={{ width: 32, height: 32, borderRadius: "50%", background: "rgba(255,255,255,0.05)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 600, color: "var(--color-text-secondary)" }}>{i + 1}</div>
            <div style={{ fontSize: 15, fontWeight: 500, color: "var(--color-text-primary)" }}>{name}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── UPLOAD SCREEN ──
function UploadScreen({ onFiles }: { onFiles: (files: File[]) => void }) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "60vh", gap: 24, textAlign: "center" }}>
      <div style={{ width: 80, height: 80, borderRadius: "50%", background: "linear-gradient(135deg, rgba(138, 125, 247, 0.1), rgba(101, 83, 225, 0.2))", display: "flex", alignItems: "center", justifyContent: "center", border: "1px solid var(--color-border-primary)" }}>
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none"><path d="M12 4v12M8 8l4-4 4 4" stroke="var(--color-brand-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/><path d="M4 20h16" stroke="var(--color-text-secondary)" strokeWidth="2" strokeLinecap="round"/></svg>
      </div>
      <div>
        <div style={{ fontSize: 24, fontWeight: 600, color: "var(--color-text-primary)", marginBottom: 8 }}>AI Financial Coach</div>
        <div style={{ fontSize: 15, color: "var(--color-text-secondary)", maxWidth: 400, margin: "0 auto" }}>Upload your bank statement CSVs to get instant personalized financial analysis powered by Agentic AI.</div>
      </div>
      
      <input type="file" multiple accept=".csv" ref={fileInputRef} onChange={(e) => onFiles(Array.from(e.target.files || []))} style={{ display: "none" }} />
      
      <div style={{ display: "flex", gap: 16, marginTop: 10 }}>
        <button className="btn-primary" onClick={() => fileInputRef.current?.click()}>Upload CSV Statements</button>
      </div>
    </div>
  );
}

const TABS = ["Overview", "Debt", "Budget", "Savings", "Payoff"];

// ── ROOT ──
export default function App() {
  const [finData, setFinData] = useState<any>(null);
  const [agents, setAgents] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [tab, setTab] = useState("Overview");

  const processUpload = async (files: File[]) => {
    try {
      setLoading(true);
      setStatus("Parsing CSV statements...");
      const finJson = await parseMultipleStatements(files);
      setFinData(finJson);

      const runAgent = async (promptFn: string, finCtx: any, agentName: string) => {
        setStatus(`Running ${agentName}...`);
        const reqBody = {
          system: "You are an AI financial agent. Output valid JSON only, exactly matching the requested schema. Do not include markdown wrappers.",
          messages: [{ role: "user", content: buildPrompt(promptFn, finCtx) }],
          temperature: 0
        };
        const res = await fetch("http://localhost:3001/api/agents", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify(reqBody)
        });
        const data = await res.json();
        let cleaned = data.content.replace(/```json/g, '').replace(/```/g, '').trim();
        return JSON.parse(cleaned);
      };

      const resolvedAgents: any = {};
      resolvedAgents.debt = await runAgent(DEBT_ANALYZER_PROMPT, finJson, "Debt Agent");
      resolvedAgents.budget = await runAgent(BUDGET_COACH_PROMPT, finJson, "Budget Coach");
      resolvedAgents.savings = await runAgent(SAVINGS_PLANNER_PROMPT, finJson, "Savings Planner");
      resolvedAgents.payoff = await runAgent(PAYOFF_OPTIMIZER_PROMPT, resolvedAgents.debt, "Payoff Optimizer");

      setAgents(resolvedAgents);
    } catch (err) {
      console.error(err);
      alert("Error processing statements. Make sure backend is running on 3001.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "80vh" }}>
      <div className="skeleton-box" style={{ width: 300, height: 16, marginBottom: 12 }}></div>
      <div style={{ color: "var(--color-brand-primary)", fontWeight: 500 }}>{status}</div>
    </div>
  );

  return (
    <div style={{ padding: "40px 20px", maxWidth: 900, margin: "0 auto" }}>
      {!agents ? (
        <UploadScreen onFiles={processUpload} />
      ) : (
        <div className="animate-fade-in">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 32 }}>
            <div>
              <div style={{ fontSize: 22, fontWeight: 700, color: "var(--color-text-primary)" }}>Financial Coach Dashboard</div>
              <div style={{ fontSize: 14, color: "var(--color-text-secondary)", marginTop: 4 }}>Analyzed {finData?.summary.months_analyzed} months of data</div>
            </div>
            <button className="btn-secondary" onClick={() => setAgents(null)}>New Analysis</button>
          </div>

          <div className="glass-panel" style={{ padding: "10px", display: "flex", gap: 8, marginBottom: 32, overflowX: "auto" }}>
            {TABS.map(t => (
              <button key={t} onClick={() => setTab(t)} className={`btn-tab ${tab === t ? 'active' : ''}`}>{t}</button>
            ))}
          </div>

          {tab === "Overview" && <OverviewTab fin={finData} />}
          {tab === "Debt"     && <DebtTab     agents={agents} />}
          {tab === "Budget"   && <BudgetTab   agents={agents} />}
          {tab === "Savings"  && <SavingsTab  agents={agents} />}
          {tab === "Payoff"   && <PayoffTab   agents={agents} />}
        </div>
      )}
    </div>
  );
}
