import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Download, FileText, Loader2, Mail, X } from "lucide-react";
import { useFinancialStore } from "../../store/financialStore.js";

// ── Helpers ───────────────────────────────────────────────────────────────────
const c = (n) => {
  if (n == null) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);
};
const p = (n) => (n == null ? "—" : `${(+n).toFixed(1)}%`);
const scoreInfo = (s) => {
  if (s >= 90) return { label: "Excellent",    color: "#10B981" };
  if (s >= 70) return { label: "Good",          color: "#34D399" };
  if (s >= 50) return { label: "Fair",          color: "#F59E0B" };
  if (s >= 30) return { label: "Below Average", color: "#F97316" };
  return        { label: "Needs Attention",     color: "#EF4444" };
};

// ── Markdown → HTML ───────────────────────────────────────────────────────────
function mdToHtml(md) {
  if (!md) return "";
  return md
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/^### (.+)$/gm, '<h3 class="h3">$1</h3>')
    .replace(/^## (.+)$/gm,  '<h2 class="h2">$1</h2>')
    .replace(/^# (.+)$/gm,   '<h1 class="h1">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g,     "<em>$1</em>")
    .replace(/`(.+?)`/g,       '<code class="code">$1</code>')
    .replace(/^---$/gm,        '<hr class="hr" />')
    .replace(/^\s*[-*] (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>[\s\S]+?<\/li>)(?=\s*(?!<li>))/g, '<ul class="ul">$1</ul>')
    .replace(/\n\n+/g, '</p><p class="p">')
    .replace(/^(?!<[h1-6hulp])/gm, '<p class="p">$&')
    .replace(/(<p class="p">)(<[h1-6])/g, "$2")
    .replace(/<p class="p"><\/p>/g, "");
}

// ── Summary email HTML ────────────────────────────────────────────────────────
function buildEmailHtml({ result, now }) {
  const snap     = result?.financial_snapshot || {};
  const score    = result?.health_score ?? null;
  const insights = (result?.financial_insights || []).slice(0, 3);
  const si       = scoreInfo(score);
  const SEV_COLOR = { critical: "#EF4444", warning: "#F59E0B", positive: "#10B981", info: "#3B82F6" };
  const insRows = insights.map(ins => {
    const col = SEV_COLOR[ins.severity] || "#3B82F6";
    return `<tr><td style="padding:8px 12px;border-bottom:1px solid #F1F5F9"><span style="font-size:11px;font-weight:700;color:${col};text-transform:uppercase">${ins.severity}</span></td><td style="padding:8px 12px;border-bottom:1px solid #F1F5F9;font-size:13px;color:#334155">${ins.finding || ""}</td></tr>`;
  }).join("");
  return `<!DOCTYPE html><html><head><meta charset="UTF-8"/></head>
<body style="font-family:system-ui,-apple-system,sans-serif;margin:0;padding:20px;background:#F8FAFC">
<div style="max-width:600px;margin:0 auto">
  <div style="background:linear-gradient(135deg,#4C1D95,#0891B2);padding:28px 32px;border-radius:14px;color:white;margin-bottom:20px">
    <div style="font-size:24px;font-weight:900;letter-spacing:-0.5px;margin-bottom:4px">FinanceIQ</div>
    <div style="font-size:16px;opacity:0.85">Your Financial Health Report · ${now}</div>
  </div>
  <div style="background:white;border-radius:14px;padding:24px;margin-bottom:16px;border:1px solid #E2E8F0;text-align:center">
    <div style="font-size:13px;color:#94A3B8;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px">Financial Health Score</div>
    <div style="font-size:56px;font-weight:900;color:${si.color};line-height:1">${score != null ? Math.round(score) : "—"}</div>
    <div style="font-size:14px;color:${si.color};font-weight:700">${si.label}</div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px">
    <div style="background:white;border-radius:12px;padding:16px;border:1px solid #E2E8F0"><div style="font-size:10px;color:#94A3B8;text-transform:uppercase;font-weight:600">Income</div><div style="font-size:22px;font-weight:800;color:#10B981">${c(snap.total_income)}</div></div>
    <div style="background:white;border-radius:12px;padding:16px;border:1px solid #E2E8F0"><div style="font-size:10px;color:#94A3B8;text-transform:uppercase;font-weight:600">Expenses</div><div style="font-size:22px;font-weight:800;color:#EF4444">${c(snap.total_expenses)}</div></div>
    <div style="background:white;border-radius:12px;padding:16px;border:1px solid #E2E8F0"><div style="font-size:10px;color:#94A3B8;text-transform:uppercase;font-weight:600">Net Savings</div><div style="font-size:22px;font-weight:800;color:#8B5CF6">${c(snap.net_savings)}</div></div>
    <div style="background:white;border-radius:12px;padding:16px;border:1px solid #E2E8F0"><div style="font-size:10px;color:#94A3B8;text-transform:uppercase;font-weight:600">Savings Rate</div><div style="font-size:22px;font-weight:800;color:#F59E0B">${p(snap.savings_rate)}</div></div>
  </div>
  ${insRows ? `<div style="background:white;border-radius:12px;padding:20px;border:1px solid #E2E8F0;margin-bottom:16px"><div style="font-size:12px;font-weight:700;color:#7C3AED;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:12px">Key Insights</div><table style="width:100%;border-collapse:collapse"><tbody>${insRows}</tbody></table></div>` : ""}
  <div style="text-align:center;padding:16px;color:#94A3B8;font-size:11px;border-top:1px solid #E2E8F0;margin-top:4px">This report is for informational purposes only. Not financial advice. Generated by FinanceIQ AI Pipeline.</div>
</div></body></html>`;
}

// ── PDF HTML builder ──────────────────────────────────────────────────────────
function buildPdfHtml({ report, result }) {
  const snap     = result?.financial_snapshot || {};
  const score    = result?.health_score ?? null;
  const insights = result?.financial_insights || [];
  const budget   = result?.budget_recommendations || {};
  const savings  = result?.savings_plan || {};
  const debt     = result?.debt_plan || {};
  const si       = scoreInfo(score);
  const now      = new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
  const txCount  = snap.transaction_count || 0;

  const COLORS = ["#7C3AED","#0891B2","#10B981","#F59E0B","#EF4444","#EC4899","#8B5CF6","#06B6D4","#34D399","#FBBF24","#F87171","#F472B6"];
  const SEV_COLOR = { critical:"#EF4444", warning:"#F59E0B", positive:"#10B981", info:"#3B82F6" };
  const SEV_BG    = { critical:"#FEF2F2", warning:"#FFFBEB", positive:"#ECFDF5", info:"#EFF6FF" };

  // Insight cards
  const insightCards = insights.slice(0, 8).map((ins) => {
    const col = SEV_COLOR[ins.severity] || "#3B82F6";
    const bg  = SEV_BG[ins.severity]   || "#EFF6FF";
    return `<div style="display:flex;border-radius:10px;overflow:hidden;border:1px solid ${col}28;margin-bottom:10px;background:${bg}"><div style="width:5px;background:${col};flex-shrink:0"></div><div style="padding:11px 14px;flex:1"><div style="display:flex;align-items:center;gap:8px;margin-bottom:5px"><span style="font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:0.07em;color:${col};background:${col}18;padding:2px 8px;border-radius:20px;border:1px solid ${col}30">${ins.severity||"info"}</span><span style="font-size:11px;color:#64748B;font-weight:600">${ins.category||""}</span></div><div style="font-size:13px;color:#1E293B;line-height:1.5;font-weight:500">${ins.finding||""}</div>${ins.recommendation?`<div style="font-size:12px;color:${col};margin-top:5px;font-weight:500">&#8594; ${ins.recommendation}</div>`:""}</div></div>`;
  }).join("");

  // Budget rows with progress bars
  const allocs    = (budget.allocations || []).slice(0, 12);
  const maxSpend  = Math.max(...allocs.map(a => Math.abs(a.current_avg ?? a.current_spend ?? 0)), 1);
  const allocRows = allocs.map((a, i) => {
    const cur  = Math.abs(a.current_avg ?? a.current_spend ?? 0);
    const rec  = Math.abs(a.recommended ?? 0);
    const diff = rec - cur;
    const col  = diff > 0 ? "#10B981" : diff < 0 ? "#EF4444" : "#64748B";
    const barW = ((cur / maxSpend) * 100).toFixed(1);
    return `<tr><td style="padding:10px 12px;border-bottom:1px solid #F1F5F9;font-weight:600;color:#1E293B;font-size:13px">${a.category||"—"}</td><td style="padding:10px 12px;border-bottom:1px solid #F1F5F9;min-width:140px"><div style="display:flex;align-items:center;gap:8px"><div style="flex:1;background:#F1F5F9;border-radius:4px;height:8px;overflow:hidden;min-width:50px"><div style="height:100%;border-radius:4px;background:${COLORS[i%COLORS.length]};width:${barW}%"></div></div><span style="font-size:12px;font-weight:600;color:#334155;white-space:nowrap">${c(cur)}</span></div></td><td style="padding:10px 12px;border-bottom:1px solid #F1F5F9;text-align:right;color:${col};font-weight:700;font-size:13px">${c(rec)}</td><td style="padding:10px 12px;border-bottom:1px solid #F1F5F9;text-align:center"><span style="background:${col}15;color:${col};padding:3px 9px;border-radius:20px;font-weight:700;font-size:11px">${a.variance_pct!=null?(a.variance_pct>0?"+":"")+a.variance_pct.toFixed(1)+"%":"—"}</span></td><td style="padding:10px 12px;border-bottom:1px solid #F1F5F9;font-size:11px;color:#64748B">${a.note||""}</td></tr>`;
  }).join("");

  // Savings goal cards
  const goalCards = (savings.savings_goals || []).map((g, i) => {
    const col = COLORS[i % COLORS.length];
    return `<div style="background:white;border:1.5px solid ${col}28;border-top:3px solid ${col};border-radius:10px;padding:16px"><div style="font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:0.07em;color:${col};margin-bottom:8px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${g.label||g.goal||"Goal"}</div><div style="font-size:22px;font-weight:900;color:#1E293B;line-height:1">${c(g.target_amount)}</div><div style="font-size:10px;color:#94A3B8;margin-bottom:10px;margin-top:3px">Target Amount</div><div style="display:flex;justify-content:space-between;padding-top:10px;border-top:1px solid #F1F5F9"><div><div style="font-size:14px;font-weight:700;color:${col}">${c(g.monthly_contribution||g.monthly_savings)}</div><div style="font-size:9px;color:#94A3B8;text-transform:uppercase;letter-spacing:0.05em">Per Month</div></div><div style="text-align:right"><div style="font-size:14px;font-weight:700;color:#334155">${g.timeline_months?g.timeline_months+" mo":g.timeframe||"—"}</div><div style="font-size:9px;color:#94A3B8;text-transform:uppercase;letter-spacing:0.05em">Timeline</div></div></div></div>`;
  }).join("");

  // Debt steps
  const debtSteps = (debt.action_steps || []).map((s, i) =>
    `<div style="display:flex;align-items:flex-start;gap:12px;padding:10px 14px;border-radius:8px;background:${i%2===0?"#FAFBFF":"white"};border:1px solid #F1F5F9;margin-bottom:6px"><div style="width:24px;height:24px;border-radius:50%;background:linear-gradient(135deg,#7C3AED,#0891B2);color:white;font-size:11px;font-weight:800;text-align:center;line-height:24px;flex-shrink:0">${i+1}</div><div style="font-size:13px;color:#334155;padding-top:3px;line-height:1.4">${s}</div></div>`
  ).join("");

  // Chart 1: Expense breakdown
  const chartAllocs = allocs.slice(0, 10);
  const expenseChartBars = chartAllocs.map((a, i) => {
    const val  = Math.abs(a.current_avg ?? a.current_spend ?? 0);
    const barW = ((val / maxSpend) * 100).toFixed(1);
    return `<div style="display:flex;align-items:center;gap:10px;margin-bottom:9px"><div style="width:110px;font-size:11px;font-weight:500;color:#475569;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${a.category||"—"}</div><div style="flex:1;background:#F1F5F9;border-radius:4px;height:14px;overflow:hidden"><div style="height:100%;border-radius:4px;background:${COLORS[i%COLORS.length]};width:${barW}%"></div></div><div style="width:65px;font-size:11px;font-weight:600;color:#334155">${c(val)}</div></div>`;
  }).join("");

  // Chart 2: Financial overview
  const totalIncome   = snap.total_income   || 0;
  const totalExpenses = snap.total_expenses || 0;
  const netSavings    = snap.net_savings    || 0;
  const maxBar  = Math.max(Math.abs(totalIncome), Math.abs(totalExpenses), Math.abs(netSavings), 1);
  const savCol  = netSavings >= 0 ? "#8B5CF6" : "#EF4444";
  const summaryChart = [
    ["Total Income",   totalIncome,   "#10B981"],
    ["Total Expenses", totalExpenses, "#EF4444"],
    ["Net Savings",    netSavings,    savCol],
  ].map(([label, val, col]) =>
    `<div style="display:flex;align-items:center;gap:10px;margin-bottom:11px"><div style="width:100px;font-size:12px;font-weight:600;color:#475569;text-align:right">${label}</div><div style="flex:1;background:#F1F5F9;border-radius:4px;height:20px;overflow:hidden"><div style="height:100%;border-radius:4px;background:${col};width:${((Math.abs(val)/maxBar)*100).toFixed(1)}%"></div></div><div style="width:80px;font-size:12px;font-weight:700;color:${col}">${c(val)}</div></div>`
  ).join("");

  // Chart 3: Budget current vs recommended (pre-split into two halves)
  const budgetItems = allocs.slice(0, 8);
  const half        = Math.ceil(budgetItems.length / 2);
  const mkBudgetBar = (a) => {
    const cur  = Math.abs(a.current_avg ?? a.current_spend ?? 0);
    const rec  = Math.abs(a.recommended ?? 0);
    const curW = ((cur / maxSpend) * 100).toFixed(1);
    const recW = ((rec / maxSpend) * 100).toFixed(1);
    return `<div style="margin-bottom:11px"><div style="font-size:11px;font-weight:600;color:#334155;margin-bottom:4px">${a.category||"—"}</div><div style="display:flex;align-items:center;gap:8px;margin-bottom:3px"><div style="width:80px;font-size:10px;color:#94A3B8;text-align:right">Current</div><div style="flex:1;background:#F1F5F9;border-radius:3px;height:10px;overflow:hidden"><div style="height:100%;border-radius:3px;background:#64748B;width:${curW}%"></div></div><div style="width:55px;font-size:10px;font-weight:600;color:#64748B">${c(cur)}</div></div><div style="display:flex;align-items:center;gap:8px"><div style="width:80px;font-size:10px;color:#94A3B8;text-align:right">Recommended</div><div style="flex:1;background:#F1F5F9;border-radius:3px;height:10px;overflow:hidden"><div style="height:100%;border-radius:3px;background:#7C3AED;width:${recW}%"></div></div><div style="width:55px;font-size:10px;font-weight:600;color:#7C3AED">${c(rec)}</div></div></div>`;
  };
  const budgetLeftBars  = budgetItems.slice(0, half).map(mkBudgetBar).join("");
  const budgetRightBars = budgetItems.slice(half).map(mkBudgetBar).join("");

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>FinanceIQ Report — ${now}</title>
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;color:#1E293B;background:#fff;font-size:14px;line-height:1.6}
    @page{size:A4;margin:0}
    @media print{body{-webkit-print-color-adjust:exact;print-color-adjust:exact}.no-print{display:none!important}.page-break{page-break-before:always}}
    .header{background:linear-gradient(135deg,#4C1D95 0%,#6D28D9 40%,#0891B2 100%);padding:32px 48px 28px;color:white;position:relative;overflow:hidden}
    .header::after{content:'';position:absolute;top:-60px;right:-60px;width:220px;height:220px;border-radius:50%;background:rgba(255,255,255,0.06)}
    .header::before{content:'';position:absolute;bottom:-40px;left:200px;width:160px;height:160px;border-radius:50%;background:rgba(255,255,255,0.04)}
    .logo-row{display:flex;align-items:center;gap:12px;margin-bottom:20px}
    .logo-box{width:42px;height:42px;border-radius:10px;background:rgba(255,255,255,0.2);display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:900;color:white;border:1.5px solid rgba(255,255,255,0.35)}
    .logo-text{font-size:22px;font-weight:900;letter-spacing:-0.5px}
    .logo-sub{font-size:10px;opacity:0.7;letter-spacing:0.12em;text-transform:uppercase;margin-top:1px}
    .header-title{font-size:28px;font-weight:800;letter-spacing:-0.5px;margin-bottom:6px}
    .header-meta{font-size:12px;opacity:0.75;display:flex;gap:20px;flex-wrap:wrap}
    .score-strip{background:#F8FAFC;border-bottom:1px solid #E2E8F0;padding:24px 48px;display:grid;grid-template-columns:110px 1fr 1fr 1fr 1fr;gap:20px;align-items:center}
    .score-circle{width:96px;height:96px;border-radius:50%;display:flex;flex-direction:column;align-items:center;justify-content:center;border:4px solid;flex-shrink:0;padding:8px}
    .score-num{font-size:26px;font-weight:900;line-height:1}
    .score-lbl{font-size:8px;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;opacity:0.85;margin-top:3px;text-align:center;word-break:break-word;max-width:72px;line-height:1.2}
    .metric{display:flex;flex-direction:column;gap:3px;padding-left:20px;border-left:2px solid #E2E8F0}
    .metric-label{font-size:10px;color:#94A3B8;font-weight:600;text-transform:uppercase;letter-spacing:0.06em}
    .metric-value{font-size:18px;font-weight:800;color:#1E293B}
    .metric-sub{font-size:10px;color:#64748B}
    .section{padding:28px 48px}
    .section-alt{background:#FAFBFF}
    .section-title{font-size:13px;font-weight:800;text-transform:uppercase;letter-spacing:0.1em;color:#7C3AED;margin-bottom:16px;display:flex;align-items:center;gap:8px}
    .section-title::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,#E2E8F0,transparent)}
    .h1{font-size:22px;font-weight:800;color:#0F172A;margin:16px 0 8px}
    .h2{font-size:16px;font-weight:700;color:#1E293B;margin:20px 0 8px;padding-bottom:6px;border-bottom:2px solid #7C3AED;display:inline-block}
    .h3{font-size:14px;font-weight:700;color:#334155;margin:14px 0 6px}
    .p{color:#475569;font-size:13.5px;line-height:1.75;margin-bottom:10px}
    .ul{padding-left:20px;margin:8px 0 12px}
    .ul li{color:#475569;font-size:13px;margin-bottom:4px}
    .code{font-family:monospace;background:#F1F5F9;padding:1px 5px;border-radius:3px;font-size:12px;color:#7C3AED}
    .hr{border:none;border-top:1px solid #E2E8F0;margin:20px 0}
    table{width:100%;border-collapse:collapse;font-size:13px}
    thead{background:linear-gradient(135deg,#4C1D95,#6D28D9);color:white}
    thead th{padding:10px 12px;text-align:left;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.05em}
    tbody tr:nth-child(even){background:#FAFBFF}
    .strategy-badge{display:inline-block;padding:5px 14px;border-radius:20px;font-size:12px;font-weight:700;text-transform:uppercase;background:linear-gradient(135deg,#7C3AED22,#0891B222);color:#7C3AED;border:1px solid #7C3AED30;margin-bottom:12px}
    .debt-metric{display:inline-block;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:12px 20px;margin-right:12px;margin-bottom:12px;text-align:center}
    .debt-metric-val{font-size:20px;font-weight:800;color:#7C3AED}
    .debt-metric-lbl{font-size:10px;color:#94A3B8;text-transform:uppercase;letter-spacing:0.06em}
    .ef-card{background:linear-gradient(135deg,#ECFDF5,#F0FDF4);border:1.5px solid #86EFAC;border-radius:12px;padding:20px;margin-bottom:16px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}
    .ef-item-val{font-size:18px;font-weight:800;color:#059669}
    .ef-item-lbl{font-size:10px;color:#6B7280;text-transform:uppercase;letter-spacing:0.05em}
    .chart-panel{background:white;border:1px solid #E2E8F0;border-radius:12px;padding:20px}
    .chart-title{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;color:#64748B;margin-bottom:14px;padding-bottom:8px;border-bottom:1px solid #F1F5F9}
    .footer{padding:20px 48px;background:#0F172A;color:white;display:flex;align-items:center;justify-content:space-between}
    .footer-logo{font-size:15px;font-weight:900;letter-spacing:-0.3px;color:white}
    .footer-meta{font-size:10px;color:#64748B;text-align:right}
  </style>
</head>
<body>

  <!-- HEADER -->
  <div class="header">
    <div class="logo-row">
      <div class="logo-box">IQ</div>
      <div>
        <div class="logo-text">FinanceIQ</div>
        <div class="logo-sub">AI Financial Coach · Confidential Report</div>
      </div>
    </div>
    <div class="header-title">Personal Financial Analysis</div>
    <div class="header-meta">
      <span>&#128197; ${now}</span>
      <span>&#128202; ${txCount} transactions analysed</span>
      <span>&#129302; 6-Agent AI Pipeline</span>
      <span>&#128274; For personal use only</span>
    </div>
  </div>

  <!-- SCORE + METRICS -->
  <div class="score-strip">
    <div class="score-circle" style="border-color:${si.color};color:${si.color}">
      <div class="score-num">${score != null ? Math.round(score) : "—"}</div>
      <div class="score-lbl">${si.label}</div>
    </div>
    <div class="metric">
      <div class="metric-label">Total Income</div>
      <div class="metric-value" style="color:#10B981">${c(snap.total_income)}</div>
      <div class="metric-sub">Period total</div>
    </div>
    <div class="metric">
      <div class="metric-label">Total Expenses</div>
      <div class="metric-value" style="color:#EF4444">${c(snap.total_expenses)}</div>
      <div class="metric-sub">Period total</div>
    </div>
    <div class="metric">
      <div class="metric-label">Net Savings</div>
      <div class="metric-value" style="color:${(snap.net_savings||0)>=0?"#8B5CF6":"#EF4444"}">${c(snap.net_savings)}</div>
      <div class="metric-sub">Income &#8722; Expenses</div>
    </div>
    <div class="metric">
      <div class="metric-label">Savings Rate</div>
      <div class="metric-value" style="color:${(snap.savings_rate||0)>20?"#10B981":"#F59E0B"}">${p(snap.savings_rate)}</div>
      <div class="metric-sub">of income saved</div>
    </div>
  </div>

  <!-- AI REPORT -->
  <div class="section">
    <div class="section-title">AI Analysis Report</div>
    ${mdToHtml(report)}
  </div>

  ${insightCards ? `
  <!-- KEY INSIGHTS -->
  <div class="section section-alt page-break">
    <div class="section-title">Key Financial Insights</div>
    ${insightCards}
  </div>` : ""}

  ${(expenseChartBars || summaryChart) ? `
  <!-- CHARTS -->
  <div class="section ${insightCards ? "" : "page-break"}">
    <div class="section-title">Visual Analysis</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px">
      ${expenseChartBars ? `<div class="chart-panel"><div class="chart-title">Spending by Category</div>${expenseChartBars}</div>` : ""}
      <div class="chart-panel">
        <div class="chart-title">Financial Overview</div>
        ${summaryChart}
        ${snap.savings_rate != null ? `
        <div style="margin-top:14px;padding-top:12px;border-top:1px solid #F1F5F9">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <span style="font-size:11px;font-weight:600;color:#475569">Savings Rate</span>
            <span style="font-size:14px;font-weight:800;color:${(snap.savings_rate||0)>20?"#10B981":"#F59E0B"}">${p(snap.savings_rate)}</span>
          </div>
          <div style="background:#F1F5F9;border-radius:4px;height:8px;overflow:hidden;position:relative">
            <div style="height:100%;border-radius:4px;background:linear-gradient(90deg,#EF4444 0%,#F59E0B 20%,#10B981 60%,#10B981 100%);width:100%"></div>
            <div style="position:absolute;top:0;left:${Math.min(99,Math.max(1,snap.savings_rate||0))}%;height:100%;width:3px;background:#1E293B;transform:translateX(-50%);border-radius:2px"></div>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:9px;color:#94A3B8;margin-top:3px"><span>0%</span><span>Target 20%+</span><span>50%</span></div>
        </div>` : ""}
      </div>
    </div>
    ${(budgetLeftBars || budgetRightBars) ? `
    <div class="chart-panel">
      <div class="chart-title">Budget: Current vs Recommended</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">
        <div>${budgetLeftBars}</div>
        <div>${budgetRightBars}</div>
      </div>
    </div>` : ""}
  </div>` : ""}

  ${allocRows ? `
  <!-- BUDGET ALLOCATIONS -->
  <div class="section section-alt page-break">
    <div class="section-title">Budget Allocation Plan</div>
    ${budget.monthly_summary ? `<p class="p" style="margin-bottom:16px">${budget.monthly_summary}</p>` : ""}
    <table>
      <thead><tr><th>Category</th><th>Current Spend</th><th style="text-align:right">Recommended</th><th style="text-align:center">Change</th><th>Note</th></tr></thead>
      <tbody>${allocRows}</tbody>
    </table>
    ${budget.surplus != null ? `<div style="margin-top:14px;text-align:right;font-size:13px;color:#64748B">Projected monthly surplus: <strong style="color:${(budget.surplus||0)>=0?"#10B981":"#EF4444"};font-size:16px">${c(budget.surplus)}</strong></div>` : ""}
  </div>` : ""}

  ${(savings.emergency_fund || goalCards || (savings.quick_wins||[]).length) ? `
  <!-- SAVINGS PLAN -->
  <div class="section ${allocRows ? "" : "page-break"}">
    <div class="section-title">Savings Strategy</div>
    ${savings.emergency_fund ? `
    <p style="font-size:12px;font-weight:700;color:#059669;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px">Emergency Fund</p>
    <div class="ef-card">
      <div><div class="ef-item-val">${c(savings.emergency_fund.target_amount)}</div><div class="ef-item-lbl">Target Amount</div></div>
      <div><div class="ef-item-val">${c(savings.emergency_fund.monthly_contribution)}/mo</div><div class="ef-item-lbl">Monthly Contribution</div></div>
      <div><div class="ef-item-val">${savings.emergency_fund.months_to_target?savings.emergency_fund.months_to_target+" months":"—"}</div><div class="ef-item-lbl">Timeline</div></div>
    </div>` : ""}
    ${goalCards ? `
    <p style="font-size:12px;font-weight:700;color:#7C3AED;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:10px${savings.emergency_fund?";margin-top:20px":""}">Savings Goals</p>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px">${goalCards}</div>` : ""}
    ${(savings.quick_wins||[]).length ? `
    <p style="font-size:12px;font-weight:700;color:#D97706;text-transform:uppercase;letter-spacing:0.06em;margin:16px 0 8px">Quick Wins</p>
    <ol style="padding-left:20px">${(savings.quick_wins||[]).map(w=>`<li style="color:#475569;font-size:13px;margin-bottom:6px">${w}</li>`).join("")}</ol>` : ""}
  </div>` : ""}

  ${debt.has_debt ? `
  <!-- DEBT STRATEGY -->
  <div class="section section-alt page-break">
    <div class="section-title">Debt Strategy</div>
    <div class="strategy-badge">${(debt.strategy||"custom").toUpperCase()} STRATEGY</div>
    ${debt.strategy_reason?`<p class="p">${debt.strategy_reason}</p>`:""}
    <div>
      <div class="debt-metric"><div class="debt-metric-val">${c(debt.monthly_paydown_target)}</div><div class="debt-metric-lbl">Monthly Paydown</div></div>
      ${debt.timeline_months?`<div class="debt-metric"><div class="debt-metric-val">${debt.timeline_months} mo</div><div class="debt-metric-lbl">Timeline</div></div>`:""}
    </div>
    ${debtSteps?`<p style="font-size:12px;font-weight:700;color:#7C3AED;text-transform:uppercase;letter-spacing:0.06em;margin:16px 0 8px">Action Steps</p><div>${debtSteps}</div>`:""}
  </div>` : ""}

  <!-- FOOTER (print-only, no on-screen bar) -->
  <div class="footer">
    <div>
      <div class="footer-logo">FinanceIQ</div>
      <div style="font-size:10px;color:#475569;margin-top:2px">AI Financial Coach &middot; Powered by LangGraph &amp; OpenRouter</div>
    </div>
    <div class="footer-meta">
      <div>Generated ${now}</div>
      <div style="margin-top:2px">For informational purposes only. Not financial advice.</div>
      <div>Consult a qualified financial advisor.</div>
    </div>
  </div>

  <script>
    window.addEventListener('load', function() {
      setTimeout(function() { window.print(); }, 600);
    });
  </script>
</body>
</html>`;
}

// ── Mailto fallback builder ───────────────────────────────────────────────────
function buildMailtoLink(to, result) {
  const snap  = result?.financial_snapshot || {};
  const score = result?.health_score;
  const now   = new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
  const lines = [
    `FinanceIQ Financial Report — ${now}`,
    ``,
    `Health Score: ${score != null ? Math.round(score) : "—"}/100`,
    ``,
    `SUMMARY`,
    `  Income:       ${c(snap.total_income)}`,
    `  Expenses:     ${c(snap.total_expenses)}`,
    `  Net Savings:  ${c(snap.net_savings)}`,
    `  Savings Rate: ${p(snap.savings_rate)}`,
    ``,
    `TOP INSIGHTS`,
    ...(result?.financial_insights || []).slice(0, 3).map(
      i => `  [${(i.severity || "info").toUpperCase()}] ${i.category}: ${i.finding}`
    ),
    ``,
    `Generated by FinanceIQ · AI Financial Coach`,
    `For informational purposes only. Not financial advice.`,
  ];
  const subject = encodeURIComponent(`FinanceIQ Financial Report — ${now}`);
  const body    = encodeURIComponent(lines.join("\n"));
  return `mailto:${encodeURIComponent(to)}?subject=${subject}&body=${body}`;
}

// ── Component ─────────────────────────────────────────────────────────────────
export default function ReportTab({ report, result }) {
  const { config } = useFinancialStore();
  const [generating, setGenerating]   = useState(false);
  const [showEmail, setShowEmail]     = useState(false);
  const [emailTo, setEmailTo]         = useState("");
  const [emailStatus, setEmailStatus] = useState(null);
  const [sending, setSending]         = useState(false);

  const handleDownloadPdf = () => {
    setGenerating(true);
    try {
      const html = buildPdfHtml({ report, result });
      const win  = window.open("", "_blank", "width=900,height=700,scrollbars=yes");
      if (!win) {
        alert("Pop-up blocked. Please allow pop-ups for this site and try again.");
        setGenerating(false);
        return;
      }
      win.document.write(html);
      win.document.close();
    } finally {
      setTimeout(() => setGenerating(false), 1500);
    }
  };

  // Open default mail client with plain-text summary pre-filled
  const handleOpenMailApp = () => {
    if (!emailTo) return;
    window.location.href = buildMailtoLink(emailTo, result);
  };

  const handleSendEmail = async () => {
    if (!emailTo) return;
    setSending(true);
    setEmailStatus(null);
    try {
      const now     = new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
      const html    = buildEmailHtml({ result, now });
      const pdfHtml = buildPdfHtml({ report, result });
      const res     = await fetch("/api/send-report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to: emailTo,
          subject: `Your FinanceIQ Financial Report — ${now}`,
          html,
          pdfHtml,
          brevoApiKey:    config.brevoApiKey    || undefined,
          brevoFromEmail: config.brevoFromEmail || undefined,
        }),
      });
      const data = await res.json();
      if (data.success) {
        const attachNote = data.hasAttachment ? " with PDF attached" : "";
        setEmailStatus({ ok: true, msg: `Report sent to ${emailTo}${attachNote}` });
        setTimeout(() => { setShowEmail(false); setEmailStatus(null); }, 3000);
      } else if (data.error?.includes("No email providers configured")) {
        setEmailStatus({
          ok: false,
          msg: "Email not configured. Check your .env file and restart the server.",
        });
      } else if (data.error?.includes("credentials invalid") || data.error?.includes("authentication failed") || data.error?.includes("Authentication")) {
        setEmailStatus({
          ok: false,
          msg: "Brevo authentication failed. Verify BREVO_SMTP_KEY and BREVO_FROM_EMAIL in .env and restart the server.",
        });
      } else {
        setEmailStatus({ ok: false, msg: data.error || "Failed to send email" });
      }
    } catch {
      setEmailStatus({ ok: false, msg: "Cannot reach server — is it running on port 3001?" });
    } finally {
      setSending(false);
    }
  };

  if (!report) return (
    <div className="text-center py-12 text-slate-500">No report available.</div>
  );

  return (
    <div className="flex flex-col gap-4">
      {/* Action bar */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <FileText size={14} className="text-accent-purple" />
          <span className="text-white text-sm font-semibold">Financial Report</span>
          <span className="text-slate-600 text-xs">AI-generated · for personal use only</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setShowEmail(true); setEmailStatus(null); }}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold glass glass-hover text-slate-300 border border-white/10"
          >
            <Mail size={13} />
            Email Report
          </button>
          <button
            onClick={handleDownloadPdf}
            disabled={generating}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all"
            style={{
              background: generating ? "rgba(139,92,246,0.1)" : "linear-gradient(135deg,#7C3AED,#0891B2)",
              color: generating ? "#64748B" : "#fff",
              border: generating ? "1px solid rgba(255,255,255,0.08)" : "none",
              boxShadow: generating ? "none" : "0 4px 16px rgba(124,58,237,0.35)",
            }}
          >
            {generating ? <><Loader2 size={14} className="animate-spin" /> Preparing…</> : <><Download size={14} /> Download PDF</>}
          </button>
        </div>
      </div>

      {/* Email modal */}
      {showEmail && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowEmail(false)}>
          <div className="glass rounded-2xl p-6 w-full max-w-sm mx-4 border border-white/10" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Mail size={16} className="text-accent-purple" />
                <span className="text-white font-semibold">Email Report</span>
              </div>
              <button onClick={() => setShowEmail(false)} className="text-slate-500 hover:text-white">
                <X size={16} />
              </button>
            </div>
            <input
              type="email"
              placeholder="recipient@example.com"
              value={emailTo}
              onChange={e => setEmailTo(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSendEmail()}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-sm mb-3 outline-none focus:border-purple-500"
            />
            {/* Primary: server-side HTML email */}
            <button
              onClick={handleSendEmail}
              disabled={!emailTo || sending}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white mb-2"
              style={{ background: "linear-gradient(135deg,#7C3AED,#0891B2)", opacity: (!emailTo || sending) ? 0.5 : 1 }}
            >
              <Mail size={13} />
              {sending ? "Sending…" : "Send Report Email"}
            </button>
            {/* Secondary: open mail client with plain-text summary */}
            <button
              onClick={() => { handleOpenMailApp(); setShowEmail(false); }}
              disabled={!emailTo}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-slate-300 glass glass-hover mb-3"
              style={{ opacity: !emailTo ? 0.4 : 1 }}
            >
              Open in Mail App
            </button>
            <button onClick={() => setShowEmail(false)} className="w-full text-center text-slate-600 text-xs hover:text-slate-400">
              Cancel
            </button>
            {emailStatus && (
              <div className={`mt-3 p-3 rounded-xl text-xs leading-relaxed ${
                emailStatus.ok ? "bg-green-500/10 border border-green-500/20 text-green-400"
                               : "bg-red-500/10 border border-red-500/20 text-red-400"
              }`}>
                {emailStatus.msg}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Report preview */}
      <div
        className="glass rounded-2xl p-6 prose prose-invert prose-sm max-w-none"
        style={{
          "--tw-prose-body":       "#CBD5E1",
          "--tw-prose-headings":   "#F1F5F9",
          "--tw-prose-links":      "#8B5CF6",
          "--tw-prose-bold":       "#F1F5F9",
          "--tw-prose-code":       "#A78BFA",
          "--tw-prose-pre-bg":     "rgba(255,255,255,0.03)",
          "--tw-prose-th-borders": "rgba(255,255,255,0.1)",
          "--tw-prose-td-borders": "rgba(255,255,255,0.06)",
          "--tw-prose-hr":         "rgba(255,255,255,0.08)",
        }}
      >
        <ReactMarkdown
          components={{
            h1: ({ children }) => <h1 className="gradient-text text-2xl font-bold mb-4">{children}</h1>,
            h2: ({ children }) => <h2 className="text-white text-lg font-semibold mt-6 mb-3 pb-2 border-b border-white/10">{children}</h2>,
            h3: ({ children }) => <h3 className="text-white/90 text-base font-semibold mt-4 mb-2">{children}</h3>,
            p:  ({ children }) => <p className="text-slate-300 text-sm leading-relaxed mb-3">{children}</p>,
            ul: ({ children }) => <ul className="flex flex-col gap-1.5 mb-3 ml-4">{children}</ul>,
            li: ({ children }) => (
              <li className="flex items-start gap-2 text-slate-300 text-sm">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-purple mt-2 flex-shrink-0" />
                <span>{children}</span>
              </li>
            ),
            strong:     ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
            code:       ({ children }) => <code className="font-mono text-accent-purple bg-white/5 px-1.5 py-0.5 rounded text-xs">{children}</code>,
            blockquote: ({ children }) => <blockquote className="border-l-2 border-accent-purple pl-4 my-3 text-slate-400 italic">{children}</blockquote>,
            hr:  () => <hr className="border-white/10 my-6" />,
            table: ({ children }) => <div className="overflow-x-auto mb-4"><table className="w-full text-sm border-collapse">{children}</table></div>,
            th: ({ children }) => <th className="text-left text-slate-400 text-xs font-semibold px-3 py-2 border-b border-white/10 bg-white/[0.02]">{children}</th>,
            td: ({ children }) => <td className="text-slate-300 text-xs px-3 py-2 border-b border-white/5">{children}</td>,
          }}
        >
          {report}
        </ReactMarkdown>
      </div>

      <p className="text-slate-700 text-[10px] text-center">
        For informational purposes only · Not financial advice · Consult a qualified financial advisor
      </p>
    </div>
  );
}
