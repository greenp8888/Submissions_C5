export const fmt = {
  currency: (n, decimals = 0) => {
    if (n == null) return "—";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: decimals,
      minimumFractionDigits: decimals,
    }).format(n);
  },
  pct: (n, decimals = 1) => {
    if (n == null) return "—";
    return `${(+n).toFixed(decimals)}%`;
  },
  compact: (n) => {
    if (n == null) return "—";
    if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
    if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
    return `$${n.toFixed(0)}`;
  },
  number: (n) => {
    if (n == null) return "—";
    return new Intl.NumberFormat("en-US").format(n);
  },
};

export function scoreLabel(score) {
  if (score >= 90) return { label: "Excellent", color: "#10B981" };
  if (score >= 70) return { label: "Good", color: "#34D399" };
  if (score >= 50) return { label: "Fair", color: "#F59E0B" };
  if (score >= 30) return { label: "Below Average", color: "#F97316" };
  return { label: "Needs Work", color: "#EF4444" };
}

export function severityColor(severity) {
  switch ((severity || "").toLowerCase()) {
    case "critical": return { bg: "rgba(239,68,68,0.1)", border: "rgba(239,68,68,0.3)", text: "#F87171", badge: "badge-critical" };
    case "warning":  return { bg: "rgba(245,158,11,0.1)", border: "rgba(245,158,11,0.3)", text: "#FCD34D", badge: "badge-warning" };
    case "positive": return { bg: "rgba(16,185,129,0.1)", border: "rgba(16,185,129,0.3)", text: "#6EE7B7", badge: "badge-positive" };
    default:         return { bg: "rgba(59,130,246,0.1)", border: "rgba(59,130,246,0.3)", text: "#93C5FD", badge: "badge-info" };
  }
}

export function clamp(val, min, max) {
  return Math.min(Math.max(val, min), max);
}
