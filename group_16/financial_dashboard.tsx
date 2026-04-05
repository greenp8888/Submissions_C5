import { useState, useRef, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, CartesianGrid } from "recharts";

// ── Demo data (mirrors what parseMultipleStatements returns + agent outputs) ──

const DEMO_FINANCIAL = {
  summary: {
    months_analyzed: 3, months_list: ["2026-01","2026-02","2026-03"],
    avg_monthly_income: 7083.33, avg_monthly_spend: 4210.40,
    avg_monthly_surplus: 2872.93, opening_balance: 4250, closing_balance: 14365.62, net_change: 10115.62,
  },
  income: { avg_monthly: 7083.33, sources: [
    { source: "Acme Corp Payroll", total: 19200, occurrences: 6 },
    { source: "Freelance Invoice #112", total: 850, occurrences: 1 },
  ]},
  spending: { avg_monthly: 4210.40, by_category: [
    { category: "Housing",       avg_monthly: 1450,   total_spent: 4350,  top_merchants: ["Oakwood Apartments ($4350)"] },
    { category: "Debt Payment",  avg_monthly: 492,    total_spent: 1476,  top_merchants: ["Navient ($861)", "Chase Visa ($255)", "Discover ($195)"] },
    { category: "Groceries",     avg_monthly: 326.70, total_spent: 980.1, top_merchants: ["Whole Foods ($559)", "Trader Joes ($420)"] },
    { category: "Dining",        avg_monthly: 183.45, total_spent: 550.35,top_merchants: ["Nobu ($142)", "Cheesecake Factory ($76)", "Doordash ($104)"] },
    { category: "Shopping",      avg_monthly: 216.62, total_spent: 649.85,top_merchants: ["Amazon.com ($390)", "Target ($225)"] },
    { category: "Transport",     avg_monthly: 132.88, total_spent: 398.65,top_merchants: ["Shell Gas ($310)", "Uber ($73)"] },
    { category: "Subscriptions", avg_monthly: 99.42,  total_spent: 298.26,top_merchants: ["Spotify ($30)", "Netflix ($46)", "Hulu ($54)"] },
    { category: "Health",        avg_monthly: 78.24,  total_spent: 234.73,top_merchants: ["Planet Fitness ($75)", "CVS ($62)"] },
    { category: "Utilities",     avg_monthly: 138.04, total_spent: 414.13,top_merchants: ["Comcast ($240)", "Con Edison ($174)"] },
  ]},
  debts: [
    { account_name: "Navient Student Loan",  monthly_payment: 287,  payments_found: 3 },
    { account_name: "Chase Visa",            monthly_payment: 85,   payments_found: 3 },
    { account_name: "Discover Card",         monthly_payment: 65,   payments_found: 3 },
    { account_name: "Capital One",           monthly_payment: 55,   payments_found: 3 },
  ],
  subscriptions: [
    { name: "Netflix",      monthly_cost: 15.49 },
    { name: "Spotify",      monthly_cost: 9.99  },
    { name: "Hulu",         monthly_cost: 17.99 },
    { name: "Amazon Prime", monthly_cost: 14.99 },
    { name: "Apple.com",    monthly_cost: 2.99  },
  ],
};

const DEMO_AGENTS = {
  debt: {
    summary: { total_monthly_debt_payments: 492, estimated_total_balance: 31400, debt_to_income_ratio: 0.069, accounts_found: 4 },
    accounts: [
      { name: "Navient Student Loan", type: "student_loan",  monthly_payment: 287, estimated_balance: 24000, estimated_apr: 5.5,  is_minimum_payment_only: true,  urgency_rank: 2 },
      { name: "Chase Visa",           type: "credit_card",   monthly_payment: 85,  estimated_balance: 3800,  estimated_apr: 22.9, is_minimum_payment_only: true,  urgency_rank: 1 },
      { name: "Discover Card",        type: "credit_card",   monthly_payment: 65,  estimated_balance: 2400,  estimated_apr: 21.4, is_minimum_payment_only: true,  urgency_rank: 2 },
      { name: "Capital One",          type: "credit_card",   monthly_payment: 55,  estimated_balance: 1200,  estimated_apr: 19.9, is_minimum_payment_only: true,  urgency_rank: 3 },
    ],
    flags: ["All 4 accounts appear to be minimum payments only — interest is compounding on $31,400 in debt", "Credit card balances total $7,400 at ~21% APR average"],
  },
  budget: {
    summary: { avg_monthly_income: 7083, avg_monthly_expenses: 4210, avg_monthly_surplus: 2873, months_analyzed: 3 },
    top_overspend_findings: [
      "Dining averaged $183/month — $142 of that was a single Nobu visit in March. Even excluding that, you're at $41/month over the 5% target.",
      "Shopping averaged $217/month driven by Amazon ($390 total) and a $199 single order in March. Consider a 48-hour rule before large purchases.",
      "Subscriptions cost $61.45/month across 5 services. You're paying for Hulu and Netflix simultaneously — that's $33/month for overlapping streaming.",
    ],
    action_items: [
      { priority: 1, action: "Cancel one of Hulu or Netflix — you're paying $33.48/month for both. Pick one.", estimated_monthly_saving: 17 },
      { priority: 2, action: "Set a $100/month dining budget. Your March Nobu visit alone was 78% of a reasonable dining budget.", estimated_monthly_saving: 83 },
      { priority: 3, action: "Batch Amazon orders — 6 separate orders across 3 months. Consolidating saves on impulse adds.", estimated_monthly_saving: 40 },
    ],
  },
  savings: {
    income_analysis: { avg_monthly_income: 7083, is_income_variable: true, conservative_monthly_income: 6400 },
    savings_assessment: { current_monthly_surplus: 2873, current_savings_rate_pct: 40.6, recommended_monthly_savings: 1200, recommended_savings_rate_pct: 17 },
    emergency_fund: { target_amount: 12600, estimated_current_amount: 4250, gap: 8350, months_to_fund_at_recommended_rate: 7 },
    goals: [
      { priority: 1, name: "Emergency fund (3 months expenses)", target_amount: 12600, monthly_contribution: 800, months_to_reach: 7,  rationale: "You have $4,250 today. At $800/month you hit your target in 7 months." },
      { priority: 2, name: "Credit card payoff fund",            target_amount: 7400,  monthly_contribution: 300, months_to_reach: 10, rationale: "Eliminating $7,400 in 22% APR debt saves ~$1,600/year in interest." },
      { priority: 3, name: "General investment account",         target_amount: 10000, monthly_contribution: 100, months_to_reach: 24, rationale: "Start small — $100/month once emergency fund is fully funded." },
    ],
  },
  payoff: {
    inputs: { total_monthly_minimum_payments: 492, estimated_extra_monthly_payment: 720, total_estimated_balance: 31400 },
    avalanche: { payoff_order: ["Chase Visa", "Discover Card", "Capital One", "Navient Student Loan"], total_months_to_payoff: 38, total_interest_paid: 4820 },
    snowball:  { payoff_order: ["Capital One", "Discover Card", "Chase Visa", "Navient Student Loan"], total_months_to_payoff: 41, total_interest_paid: 6390 },
    comparison: { interest_saved_with_avalanche: 1570, time_difference_months: 3, recommendation: "avalanche", recommendation_rationale: "Avalanche saves you $1,570 in interest and finishes 3 months sooner. The math is clear — go avalanche." },
  },
};

// ── Palette ──
const COLORS = ["#7F77DD","#1D9E75","#D85A30","#378ADD","#BA7517","#D4537E","#639922","#888780","#E24B4A"];
const fmt = (n) => "$" + Number(n).toLocaleString("en-US", { maximumFractionDigits: 0 });
const fmtK = (n) => n >= 1000 ? "$" + (n/1000).toFixed(1) + "k" : fmt(n);

// ── Sub-components ──

function StatCard({ label, value, sub, accent }) {
  return (
    <div style={{ background: "var(--color-background-secondary)", borderRadius: "var(--border-radius-lg)", padding: "14px 16px", flex: 1, minWidth: 0 }}>
      <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 500, color: accent || "var(--color-text-primary)" }}>{value}</div>
      {sub && <div style={{ fontSize: 12, color: "var(--color-text-tertiary)", marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

function SectionHeader({ title }) {
  return <div style={{ fontSize: 13, fontWeight: 500, color: "var(--color-text-primary)", margin: "24px 0 10px" }}>{title}</div>;
}

function Flag({ text, color }) {
  const bg   = color === "red"    ? "var(--color-background-danger)"  : color === "amber" ? "var(--color-background-warning)" : "var(--color-background-info)";
  const fg   = color === "red"    ? "var(--color-text-danger)"        : color === "amber" ? "var(--color-text-warning)"       : "var(--color-text-info)";
  return (
    <div style={{ background: bg, color: fg, fontSize: 12, padding: "7px 10px", borderRadius: "var(--border-radius-md)", lineHeight: 1.5, marginBottom: 6 }}>{text}</div>
  );
}

// ── Tabs ──
const TABS = ["Overview", "Debt", "Budget", "Savings", "Payoff", "Chat"];

// ── OVERVIEW TAB ──
function OverviewTab({ fin, agents }) {
  const spendData = fin.spending.by_category
    .filter(c => c.category !== "Debt Payment")
    .sort((a,b) => b.avg_monthly - a.avg_monthly)
    .slice(0, 6)
    .map(c => ({ name: c.category, value: c.avg_monthly }));

  const monthlyFlow = [
    { month: "Jan", income: 6400, spend: 4312 },
    { month: "Feb", income: 6400, spend: 4053 },
    { month: "Mar", income: 7250, spend: 4266 },
  ];

  return (
    <div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard label="Avg monthly income"  value={fmt(fin.summary.avg_monthly_income)}  sub="3-month average" />
        <StatCard label="Avg monthly spend"   value={fmt(fin.summary.avg_monthly_spend)}   sub="excl. transfers" />
        <StatCard label="Avg monthly surplus" value={fmt(fin.summary.avg_monthly_surplus)} accent="#1D9E75" sub="available to save or pay debt" />
        <StatCard label="Net balance change"  value={fmt(fin.summary.net_change)} accent="#7F77DD" sub="Jan → Mar" />
      </div>

      <SectionHeader title="Monthly cash flow" />
      <div style={{ height: 200 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={monthlyFlow} barGap={4}>
            <XAxis dataKey="month" tick={{ fontSize: 12, fill: "var(--color-text-secondary)" }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: "var(--color-text-tertiary)" }} axisLine={false} tickLine={false} tickFormatter={fmtK} width={44} />
            <Tooltip formatter={(v) => fmt(v)} contentStyle={{ fontSize: 12, borderRadius: 8, border: "0.5px solid var(--color-border-secondary)" }} />
            <Bar dataKey="income" fill="#7F77DD" radius={[4,4,0,0]} name="Income" />
            <Bar dataKey="spend"  fill="#1D9E75" radius={[4,4,0,0]} name="Spend"  />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div style={{ display: "flex", gap: 14, fontSize: 12, color: "var(--color-text-secondary)", marginTop: 6 }}>
        <span><span style={{ display:"inline-block", width:10, height:10, borderRadius:2, background:"#7F77DD", marginRight:5 }}/>Income</span>
        <span><span style={{ display:"inline-block", width:10, height:10, borderRadius:2, background:"#1D9E75", marginRight:5 }}/>Spend</span>
      </div>

      <SectionHeader title="Spend breakdown (avg/month)" />
      <div style={{ height: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={spendData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={85} innerRadius={45} paddingAngle={2}>
              {spendData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie>
            <Tooltip formatter={(v) => fmt(v)} contentStyle={{ fontSize: 12, borderRadius: 8, border: "0.5px solid var(--color-border-secondary)" }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px 14px", fontSize: 12, color: "var(--color-text-secondary)", marginTop: 4 }}>
        {spendData.map((d, i) => (
          <span key={i}><span style={{ display:"inline-block", width:10, height:10, borderRadius:2, background: COLORS[i % COLORS.length], marginRight:5 }}/>{d.name}</span>
        ))}
      </div>
    </div>
  );
}

// ── DEBT TAB ──
function DebtTab({ agents }) {
  const { debt } = agents;
  const barData = debt.accounts.map(a => ({ name: a.name.replace(" Student Loan","").replace(" Card",""), balance: a.estimated_balance, payment: a.monthly_payment }));
  return (
    <div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard label="Total estimated debt"     value={fmtK(debt.summary.estimated_total_balance)} accent="#E24B4A" />
        <StatCard label="Monthly minimums"         value={fmt(debt.summary.total_monthly_debt_payments)} sub="all accounts combined" />
        <StatCard label="Accounts found"           value={debt.summary.accounts_found} sub="all minimum payments only" />
        <StatCard label="Debt-to-income ratio"     value={(debt.summary.debt_to_income_ratio * 100).toFixed(1) + "%"} sub="monthly debt / income" accent="#BA7517" />
      </div>

      {debt.flags.map((f,i) => <Flag key={i} text={f} color="red" />)}

      <SectionHeader title="Debt accounts" />
      {debt.accounts.map((a, i) => (
        <div key={i} style={{ border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-md)", padding: "12px 14px", marginBottom: 8, background: "var(--color-background-primary)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 500, color: "var(--color-text-primary)" }}>{a.name}</div>
              <div style={{ fontSize: 12, color: "var(--color-text-tertiary)", marginTop: 2 }}>{a.type.replace("_"," ")} · {a.estimated_apr}% APR</div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 15, fontWeight: 500, color: "var(--color-text-primary)" }}>{fmtK(a.estimated_balance)}</div>
              <div style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>{fmt(a.monthly_payment)}/mo</div>
            </div>
          </div>
          <div style={{ marginTop: 10, background: "var(--color-background-tertiary)", borderRadius: 4, height: 6, overflow: "hidden" }}>
            <div style={{ height: "100%", width: Math.min(100, (a.estimated_balance / debt.summary.estimated_total_balance) * 100) + "%", background: COLORS[i], borderRadius: 4 }} />
          </div>
        </div>
      ))}

      <SectionHeader title="Balance by account" />
      <div style={{ height: 180 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={barData} layout="vertical" margin={{ left: 8 }}>
            <XAxis type="number" tick={{ fontSize: 11, fill: "var(--color-text-tertiary)" }} tickFormatter={fmtK} axisLine={false} tickLine={false} />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 12, fill: "var(--color-text-secondary)" }} axisLine={false} tickLine={false} width={90} />
            <Tooltip formatter={(v) => fmt(v)} contentStyle={{ fontSize: 12, borderRadius: 8, border: "0.5px solid var(--color-border-secondary)" }} />
            <Bar dataKey="balance" radius={[0,4,4,0]} name="Balance">
              {barData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ── BUDGET TAB ──
function BudgetTab({ fin, agents }) {
  const { budget } = agents;
  const recPct = { Housing: 30, Groceries: 15, Transport: 10, Dining: 5, Shopping: 5, Subscriptions: 5, Health: 5, Utilities: 8 };
  const cats = fin.spending.by_category.filter(c => c.category !== "Debt Payment" && c.category !== "Cash" && c.category !== "Transfer");
  const income = fin.summary.avg_monthly_income;

  return (
    <div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard label="Avg monthly surplus" value={fmt(budget.summary.avg_monthly_surplus)} accent="#1D9E75" />
        <StatCard label="Subscription total"  value={fmt(fin.subscriptions.reduce((a,s) => a + s.monthly_cost, 0).toFixed(2))} sub={fin.subscriptions.length + " active services"} />
      </div>

      <SectionHeader title="Top findings" />
      {budget.top_overspend_findings.map((f, i) => <Flag key={i} text={f} color="amber" />)}

      <SectionHeader title="Spend vs. recommended (% of income)" />
      {cats.map((c, i) => {
        const rec = recPct[c.category] || 5;
        const actual = (c.avg_monthly / income) * 100;
        const over = actual > rec;
        return (
          <div key={i} style={{ marginBottom: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 3 }}>
              <span style={{ color: "var(--color-text-primary)", fontWeight: 500 }}>{c.category}</span>
              <span style={{ color: over ? "var(--color-text-danger)" : "var(--color-text-success)" }}>
                {actual.toFixed(1)}% <span style={{ color: "var(--color-text-tertiary)" }}>/ {rec}% target</span>
              </span>
            </div>
            <div style={{ background: "var(--color-background-tertiary)", borderRadius: 4, height: 8, position: "relative", overflow: "hidden" }}>
              <div style={{ height: "100%", width: Math.min(100, (actual / rec) * 100) + "%", background: over ? "#E24B4A" : "#1D9E75", borderRadius: 4, transition: "width .3s" }} />
            </div>
            <div style={{ fontSize: 11, color: "var(--color-text-tertiary)", marginTop: 2 }}>{fmt(c.avg_monthly)}/mo · {c.top_merchants[0]}</div>
          </div>
        );
      })}

      <SectionHeader title="Action items" />
      {budget.action_items.map((a, i) => (
        <div key={i} style={{ display: "flex", gap: 10, padding: "10px 12px", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-md)", marginBottom: 8, background: "var(--color-background-primary)" }}>
          <div style={{ width: 22, height: 22, borderRadius: "50%", background: "#7F77DD22", color: "#7F77DD", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 500, flexShrink: 0, marginTop: 1 }}>{a.priority}</div>
          <div>
            <div style={{ fontSize: 13, color: "var(--color-text-primary)", lineHeight: 1.5 }}>{a.action}</div>
            {a.estimated_monthly_saving && <div style={{ fontSize: 12, color: "#1D9E75", marginTop: 3 }}>Saves ~{fmt(a.estimated_monthly_saving)}/month</div>}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── SAVINGS TAB ──
function SavingsTab({ agents }) {
  const { savings } = agents;
  const goalData = savings.goals.map(g => ({ name: g.name.split("(")[0].trim(), target: g.target_amount, monthly: g.monthly_contribution }));

  return (
    <div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard label="Current savings rate"     value={savings.savings_assessment.current_savings_rate_pct + "%"} sub="of avg monthly income" accent="#1D9E75" />
        <StatCard label="Recommended save/month"   value={fmt(savings.savings_assessment.recommended_monthly_savings)} sub="after debt minimums + goals" />
        <StatCard label="Emergency fund gap"       value={fmt(savings.emergency_fund.gap)} accent="#E24B4A" sub={savings.emergency_fund.months_to_fund_at_recommended_rate + " months to close"} />
      </div>

      <SectionHeader title="Emergency fund progress" />
      <div style={{ border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-md)", padding: "14px", background: "var(--color-background-primary)", marginBottom: 8 }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 6 }}>
          <span style={{ color: "var(--color-text-secondary)" }}>Current: <strong style={{ color: "var(--color-text-primary)" }}>{fmt(savings.emergency_fund.estimated_current_amount)}</strong></span>
          <span style={{ color: "var(--color-text-secondary)" }}>Target: <strong style={{ color: "var(--color-text-primary)" }}>{fmt(savings.emergency_fund.target_amount)}</strong></span>
        </div>
        <div style={{ background: "var(--color-background-tertiary)", borderRadius: 6, height: 12, overflow: "hidden" }}>
          <div style={{ height: "100%", width: (savings.emergency_fund.estimated_current_amount / savings.emergency_fund.target_amount * 100) + "%", background: "#7F77DD", borderRadius: 6, transition: "width .5s" }} />
        </div>
        <div style={{ fontSize: 12, color: "var(--color-text-tertiary)", marginTop: 6 }}>
          {((savings.emergency_fund.estimated_current_amount / savings.emergency_fund.target_amount) * 100).toFixed(0)}% funded · {savings.emergency_fund.months_to_fund_at_recommended_rate} months to target at {fmt(savings.goals[0].monthly_contribution)}/month
        </div>
      </div>

      <SectionHeader title="Savings goals" />
      {savings.goals.map((g, i) => (
        <div key={i} style={{ border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-md)", padding: "12px 14px", marginBottom: 8, background: "var(--color-background-primary)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 500, color: "var(--color-text-primary)" }}>{g.name}</div>
              <div style={{ fontSize: 12, color: "var(--color-text-tertiary)", marginTop: 2 }}>{g.rationale}</div>
            </div>
            <div style={{ textAlign: "right", flexShrink: 0, marginLeft: 12 }}>
              <div style={{ fontSize: 15, fontWeight: 500, color: "var(--color-text-primary)" }}>{fmt(g.target_amount)}</div>
              <div style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>{g.months_to_reach} months</div>
            </div>
          </div>
          <div style={{ marginTop: 8, background: "var(--color-background-tertiary)", borderRadius: 4, height: 6, overflow: "hidden" }}>
            <div style={{ height: "100%", width: Math.min(100, (i === 0 ? savings.emergency_fund.estimated_current_amount / g.target_amount : 0) * 100) + "%", background: COLORS[i], borderRadius: 4 }} />
          </div>
        </div>
      ))}
    </div>
  );
}

// ── PAYOFF TAB ──
function PayoffTab({ agents }) {
  const { payoff } = agents;
  const [mode, setMode] = useState("avalanche");
  const active = payoff[mode];
  const other  = payoff[mode === "avalanche" ? "snowball" : "avalanche"];

  const compData = [
    { name: "Avalanche", months: payoff.avalanche.total_months_to_payoff, interest: payoff.avalanche.total_interest_paid },
    { name: "Snowball",  months: payoff.snowball.total_months_to_payoff,  interest: payoff.snowball.total_interest_paid  },
  ];

  return (
    <div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <StatCard label="Extra/month toward debt" value={fmt(payoff.inputs.estimated_extra_monthly_payment)} sub="60% of monthly surplus" />
        <StatCard label="Total balance"           value={fmtK(payoff.inputs.total_estimated_balance)} />
        <StatCard label="Interest saved (avalanche)" value={fmt(payoff.comparison.interest_saved_with_avalanche)} accent="#1D9E75" sub={payoff.comparison.time_difference_months + " months faster"} />
      </div>

      <Flag text={"Recommendation: " + payoff.comparison.recommendation_rationale} color="blue" />

      <SectionHeader title="Strategy comparison" />
      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        {["avalanche","snowball"].map(s => (
          <button key={s} onClick={() => setMode(s)} style={{ flex: 1, padding: "8px 0", fontSize: 13, fontWeight: mode === s ? 500 : 400, borderRadius: "var(--border-radius-md)", border: mode === s ? "1.5px solid #7F77DD" : "0.5px solid var(--color-border-secondary)", background: mode === s ? "#EEEDFE" : "var(--color-background-primary)", color: mode === s ? "#3C3489" : "var(--color-text-secondary)", cursor: "pointer", transition: "all .15s" }}>
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      <div style={{ display: "flex", gap: 10, marginBottom: 16 }}>
        <StatCard label="Payoff time"    value={active.total_months_to_payoff + " mo"} />
        <StatCard label="Total interest" value={fmt(active.total_interest_paid)} accent={mode === "avalanche" ? "#1D9E75" : "#BA7517"} />
      </div>

      <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginBottom: 8, fontWeight: 500 }}>Payoff order</div>
      {active.payoff_order.map((name, i) => {
        const acct = agents.debt.accounts.find(a => a.name === name) || {};
        return (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 12px", border: "0.5px solid var(--color-border-tertiary)", borderRadius: "var(--border-radius-md)", marginBottom: 6, background: "var(--color-background-primary)" }}>
            <div style={{ width: 24, height: 24, borderRadius: "50%", background: COLORS[i] + "22", color: COLORS[i], display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 500, flexShrink: 0 }}>{i+1}</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13, fontWeight: 500, color: "var(--color-text-primary)" }}>{name}</div>
              <div style={{ fontSize: 11, color: "var(--color-text-tertiary)" }}>{acct.estimated_apr ? acct.estimated_apr + "% APR · " : ""}{acct.estimated_balance ? fmtK(acct.estimated_balance) + " balance" : ""}</div>
            </div>
            <div style={{ fontSize: 12, color: "var(--color-text-secondary)" }}>mo {active.monthly_plan?.[i]?.payoff_month ?? "—"}</div>
          </div>
        );
      })}

      <SectionHeader title="Interest paid: avalanche vs snowball" />
      <div style={{ height: 160 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={compData} barSize={60}>
            <XAxis dataKey="name" tick={{ fontSize: 12, fill: "var(--color-text-secondary)" }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: "var(--color-text-tertiary)" }} axisLine={false} tickLine={false} tickFormatter={fmtK} width={44} />
            <Tooltip formatter={(v) => fmt(v)} contentStyle={{ fontSize: 12, borderRadius: 8, border: "0.5px solid var(--color-border-secondary)" }} />
            <Bar dataKey="interest" radius={[4,4,0,0]} name="Total interest">
              <Cell fill="#1D9E75" />
              <Cell fill="#BA7517" />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ── CHAT TAB ──
function ChatTab({ fin, agents }) {
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Hi! I've analyzed your 3 months of financial data. You have $31,400 in debt, a $2,873 monthly surplus, and some clear wins available. What would you like to explore?" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const SYSTEM = `You are a friendly, direct AI financial coach. You have access to the user's financial data and agent analysis results below. Answer questions concisely, always reference specific numbers from the data. Never give generic advice — every response must cite actual figures from their data.

Financial summary: ${JSON.stringify(fin.summary)}
Debt analysis: ${JSON.stringify(agents.debt)}
Budget analysis: ${JSON.stringify(agents.budget)}
Savings plan: ${JSON.stringify(agents.savings)}
Payoff plan: ${JSON.stringify(agents.payoff)}`;

  async function send() {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", text: userMsg }]);
    setLoading(true);

    try {
      const history = messages.map(m => ({ role: m.role === "assistant" ? "assistant" : "user", content: m.text }));
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1000,
          system: SYSTEM,
          messages: [...history, { role: "user", content: userMsg }],
        }),
      });
      const data = await res.json();
      const reply = data.content?.[0]?.text || "Sorry, I couldn't get a response.";
      setMessages(prev => [...prev, { role: "assistant", text: reply }]);
    } catch {
      setMessages(prev => [...prev, { role: "assistant", text: "Connection error — please try again." }]);
    } finally {
      setLoading(false);
    }
  }

  const suggestions = ["How do I pay off debt fastest?", "Where am I overspending?", "How long to build emergency fund?"];

  return (
    <div style={{ display: "flex", flexDirection: "column", height: 520 }}>
      <div style={{ flex: 1, overflowY: "auto", paddingBottom: 8 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start", marginBottom: 10 }}>
            <div style={{ maxWidth: "82%", padding: "10px 13px", borderRadius: m.role === "user" ? "12px 12px 4px 12px" : "12px 12px 12px 4px", background: m.role === "user" ? "#7F77DD" : "var(--color-background-secondary)", color: m.role === "user" ? "#fff" : "var(--color-text-primary)", fontSize: 13, lineHeight: 1.6 }}>
              {m.text}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ display: "flex", gap: 4, padding: "10px 13px", width: 56, background: "var(--color-background-secondary)", borderRadius: "12px 12px 12px 4px" }}>
            {[0,1,2].map(i => <div key={i} style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--color-text-tertiary)", animation: `bounce 1s ${i*0.2}s infinite` }} />)}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {messages.length === 1 && (
        <div style={{ display: "flex", gap: 6, marginBottom: 10, flexWrap: "wrap" }}>
          {suggestions.map((s, i) => (
            <button key={i} onClick={() => { setInput(s); }} style={{ fontSize: 12, padding: "5px 10px", borderRadius: 20, border: "0.5px solid var(--color-border-secondary)", background: "var(--color-background-primary)", color: "var(--color-text-secondary)", cursor: "pointer" }}>{s}</button>
          ))}
        </div>
      )}

      <div style={{ display: "flex", gap: 8, borderTop: "0.5px solid var(--color-border-tertiary)", paddingTop: 10 }}>
        <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && send()} placeholder="Ask about your finances…" style={{ flex: 1, padding: "9px 12px", borderRadius: "var(--border-radius-md)", border: "0.5px solid var(--color-border-secondary)", background: "var(--color-background-primary)", fontSize: 13, color: "var(--color-text-primary)", outline: "none" }} />
        <button onClick={send} disabled={loading || !input.trim()} style={{ padding: "9px 16px", borderRadius: "var(--border-radius-md)", border: "none", background: "#7F77DD", color: "#fff", fontSize: 13, cursor: loading ? "not-allowed" : "pointer", opacity: loading || !input.trim() ? 0.5 : 1 }}>Send</button>
      </div>

      <style>{`@keyframes bounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-4px)} }`}</style>
    </div>
  );
}

// ── UPLOAD SCREEN ──
function UploadScreen({ onDemo }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: 420, gap: 20, textAlign: "center" }}>
      <div style={{ width: 56, height: 56, borderRadius: "50%", background: "#EEEDFE", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 4v12M8 8l4-4 4 4" stroke="#7F77DD" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/><path d="M4 20h16" stroke="#7F77DD" strokeWidth="1.5" strokeLinecap="round"/></svg>
      </div>
      <div>
        <div style={{ fontSize: 16, fontWeight: 500, color: "var(--color-text-primary)", marginBottom: 6 }}>Upload your bank statement</div>
        <div style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>CSV format · Up to 3 months</div>
      </div>
      <div style={{ display: "flex", gap: 10 }}>
        <button style={{ padding: "9px 20px", borderRadius: "var(--border-radius-md)", border: "0.5px solid var(--color-border-secondary)", background: "var(--color-background-primary)", color: "var(--color-text-secondary)", fontSize: 13, cursor: "pointer" }}>Upload CSV</button>
        <button onClick={onDemo} style={{ padding: "9px 20px", borderRadius: "var(--border-radius-md)", border: "none", background: "#7F77DD", color: "#fff", fontSize: 13, cursor: "pointer" }}>Use demo data</button>
      </div>
    </div>
  );
}

// ── ROOT ──
export default function App() {
  const [ready, setReady] = useState(false);
  const [tab, setTab] = useState("Overview");

  return (
    <div style={{ padding: "16px 16px 32px", maxWidth: 680, margin: "0 auto", fontFamily: "var(--font-sans)" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 500, color: "var(--color-text-primary)" }}>Financial Coach</div>
          {ready && <div style={{ fontSize: 12, color: "var(--color-text-tertiary)", marginTop: 2 }}>Jan – Mar 2026 · 3 months</div>}
        </div>
        {ready && (
          <button onClick={() => setReady(false)} style={{ fontSize: 12, padding: "5px 12px", borderRadius: "var(--border-radius-md)", border: "0.5px solid var(--color-border-secondary)", background: "var(--color-background-primary)", color: "var(--color-text-secondary)", cursor: "pointer" }}>
            New upload
          </button>
        )}
      </div>

      {!ready ? (
        <UploadScreen onDemo={() => { setReady(true); setTab("Overview"); }} />
      ) : (
        <>
          <div style={{ display: "flex", gap: 4, marginBottom: 20, flexWrap: "wrap" }}>
            {TABS.map(t => (
              <button key={t} onClick={() => setTab(t)} style={{ padding: "6px 14px", borderRadius: 20, border: tab === t ? "1.5px solid #7F77DD" : "0.5px solid var(--color-border-tertiary)", background: tab === t ? "#EEEDFE" : "transparent", color: tab === t ? "#3C3489" : "var(--color-text-secondary)", fontSize: 13, cursor: "pointer", fontWeight: tab === t ? 500 : 400, transition: "all .15s" }}>
                {t}
              </button>
            ))}
          </div>

          {tab === "Overview" && <OverviewTab fin={DEMO_FINANCIAL} agents={DEMO_AGENTS} />}
          {tab === "Debt"     && <DebtTab     agents={DEMO_AGENTS} />}
          {tab === "Budget"   && <BudgetTab   fin={DEMO_FINANCIAL} agents={DEMO_AGENTS} />}
          {tab === "Savings"  && <SavingsTab  agents={DEMO_AGENTS} />}
          {tab === "Payoff"   && <PayoffTab   agents={DEMO_AGENTS} />}
          {tab === "Chat"     && <ChatTab     fin={DEMO_FINANCIAL} agents={DEMO_AGENTS} />}
        </>
      )}
    </div>
  );
}
