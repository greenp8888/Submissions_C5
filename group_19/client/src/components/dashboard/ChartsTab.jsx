import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend,
  LineChart, Line, Area, AreaChart, ReferenceLine,
} from "recharts";
import { fmt } from "../../utils/formatters.js";

const PALETTE = ["#8B5CF6","#3B82F6","#06B6D4","#10B981","#F59E0B","#EF4444","#EC4899","#F97316","#14B8A6","#A78BFA"];

const tooltipStyle = {
  backgroundColor: "#0f1223",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: "12px",
  padding: "10px 14px",
  color: "#F1F5F9",
  fontSize: 12,
  boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
};

function ChartCard({ title, children }) {
  return (
    <div className="glass rounded-2xl p-5">
      <p className="text-white font-semibold mb-4 text-sm">{title}</p>
      {children}
    </div>
  );
}

export default function ChartsTab({ snapshot, budget }) {
  if (!snapshot) return <div className="text-center py-12 text-slate-500">No chart data.</div>;

  const { expense_by_category = {}, income_sources = {} } = snapshot;

  // Expense pie — filter zero/negative, take top 10
  const pieData = Object.entries(expense_by_category)
    .map(([name, value]) => ({ name, value: Math.abs(value) }))
    .filter(d => d.value > 0)
    .sort((a, b) => b.value - a.value)
    .slice(0, 10);

  // Income vs expense bar — clamp savings to 0 floor for bar; show sign in tooltip
  const netSavings = snapshot.net_savings || 0;
  const summaryBar = [
    { name: "Income",   value: snapshot.total_income || 0,              fill: "#10B981" },
    { name: "Expenses", value: Math.abs(snapshot.total_expenses || 0),  fill: "#EF4444" },
    { name: "Savings",  value: Math.max(0, netSavings),                 fill: "#8B5CF6" },
  ];

  // Budget comparison — field is current_avg from the agent (fallback to current_spend)
  const budgetBar = (budget?.allocations || [])
    .slice(0, 10)
    .map((a) => ({
      name: a.category?.slice(0, 16) || "Unknown",
      Current:     Math.abs(a.current_avg || a.current_spend || 0),
      Recommended: Math.abs(a.recommended || 0),
    }))
    .filter(a => a.Current > 0 || a.Recommended > 0);

  // Income sources
  const incomeBar = Object.entries(income_sources)
    .map(([name, value]) => ({ name: name.slice(0, 14), value: Math.abs(value) }))
    .sort((a, b) => b.value - a.value);

  return (
    <div className="flex flex-col gap-5">
      {/* Expense Breakdown Pie */}
      <ChartCard title="Expense Breakdown">
        <div className="flex flex-col sm:flex-row gap-4 items-center">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={90}
                paddingAngle={3}
                dataKey="value"
              >
                {pieData.map((_, i) => (
                  <Cell key={i} fill={PALETTE[i % PALETTE.length]} stroke="transparent" />
                ))}
              </Pie>
              <Tooltip
                contentStyle={tooltipStyle}
                formatter={(v) => [fmt.currency(v), "Amount"]}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-col gap-1.5 min-w-0 w-full sm:w-auto">
            {pieData.map((d, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <div className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{ background: PALETTE[i % PALETTE.length] }} />
                <span className="text-slate-400 truncate flex-1">{d.name}</span>
                <span className="text-white font-mono flex-shrink-0">{fmt.compact(d.value)}</span>
              </div>
            ))}
          </div>
        </div>
      </ChartCard>

      {/* Income vs Expenses vs Savings */}
      <ChartCard title="Financial Overview">
        {netSavings < 0 && (
          <div className="mb-3 px-3 py-2 rounded-lg text-xs flex items-center gap-2"
            style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.25)", color: "#f87171" }}>
            ⚠ Spending exceeds income by {fmt.currency(Math.abs(netSavings))} — deficit month
          </div>
        )}
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={summaryBar} barSize={48}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
            <XAxis dataKey="name" tick={{ fill: "#64748B", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#64748B", fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={fmt.compact} />
            <Tooltip contentStyle={tooltipStyle} formatter={(v, name, props) => {
              const raw = props.payload?.name === "Savings" && netSavings < 0 ? netSavings : v;
              return [fmt.currency(raw), props.payload?.name];
            }} />
            <Bar dataKey="value" radius={[8, 8, 0, 0]}>
              {summaryBar.map((d, i) => <Cell key={i} fill={d.fill} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* Budget comparison */}
      {budgetBar.length > 0 && (
        <ChartCard title="Budget: Current vs Recommended">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={budgetBar} barGap={4} barSize={12}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: "#64748B", fontSize: 9 }} axisLine={false} tickLine={false} angle={-30} textAnchor="end" height={45} />
              <YAxis tick={{ fill: "#64748B", fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={fmt.compact} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => [fmt.currency(v), ""]} />
              <Legend wrapperStyle={{ fontSize: 11, color: "#94A3B8" }} />
              <Bar dataKey="Current" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Recommended" fill="#10B981" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      )}

      {/* Income Sources */}
      {incomeBar.length > 0 && (
        <ChartCard title="Income Sources">
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={incomeBar} layout="vertical" barSize={14}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
              <XAxis type="number" tick={{ fill: "#64748B", fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={fmt.compact} />
              <YAxis dataKey="name" type="category" tick={{ fill: "#94A3B8", fontSize: 11 }} axisLine={false} tickLine={false} width={90} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => [fmt.currency(v), "Income"]} />
              <Bar dataKey="value" fill="#10B981" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      )}
    </div>
  );
}
