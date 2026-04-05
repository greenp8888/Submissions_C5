"use client";

import { useState } from "react";

interface RepoItem {
  title: string;
  url: string;
  summary: string;
  relevance_score: number;
  metadata: Record<string, any>;
}

interface SourceCardProps {
  source: string;
  items: RepoItem[];
  sentiment: string;
}

const SOURCE_LABELS: Record<string, string> = {
  github:  "GitHub",
  reddit:  "Reddit",
  hn:      "Hacker News",
  ph:      "Product Hunt",
  ai4that: "ThereIsAnAIForThat",
  yc:      "Y Combinator",
};

const SENTIMENT_META: Record<string, { color: string; bg: string; border: string }> = {
  positive:         { color: "#3fb950", bg: "rgba(35,134,54,0.18)",  border: "rgba(63,185,80,0.35)" },
  neutral:          { color: "#8b949e", bg: "rgba(139,148,158,0.1)", border: "rgba(139,148,158,0.3)" },
  negative:         { color: "#f85149", bg: "rgba(248,81,73,0.16)",  border: "rgba(248,81,73,0.35)" },
  insufficient_data:{ color: "#8b949e", bg: "rgba(139,148,158,0.08)",border: "rgba(139,148,158,0.2)" },
};

function getBarFill(score: number): string {
  if (score >= 0.7) return "linear-gradient(90deg,#2ea043,#3fb950)";
  if (score >= 0.4) return "linear-gradient(90deg,#bb8009,#d29922)";
  return "linear-gradient(90deg,#da3633,#f85149)";
}

export default function SourceCard({ source, items, sentiment }: SourceCardProps) {
  const [expanded, setExpanded] = useState(false);

  const avgRelevance = items.length
    ? items.reduce((s, i) => s + i.relevance_score, 0) / items.length
    : 0;

  const smeta = SENTIMENT_META[sentiment] ?? SENTIMENT_META.neutral;

  return (
    <div
      style={{
        background: "#161b22",
        border: "1px solid #30363d",
        borderRadius: 14,
        overflow: "hidden",
        transition: "border-color 0.2s ease",
      }}
      onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.14)"; }}
      onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "#30363d"; }}
    >
      {/* Header row */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full cursor-pointer"
        aria-expanded={expanded}
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 140px 80px 28px",
          alignItems: "center",
          gap: 12,
          padding: "14px 16px",
          background: "transparent",
          border: "none",
          textAlign: "left",
        }}
      >
        {/* Source name + sentiment pill */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
              background: smeta.color,
              boxShadow: `0 0 6px ${smeta.color}`,
            }}
          />
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 13,
              fontWeight: 600,
              letterSpacing: "0.04em",
              color: "#f0f6fc",
            }}
          >
            {SOURCE_LABELS[source] ?? source}
          </span>
          <span
            style={{
              padding: "1px 7px", borderRadius: 999, fontSize: 10,
              fontWeight: 700, fontFamily: "var(--font-mono)",
              letterSpacing: "0.06em",
              background: smeta.bg, color: smeta.color, border: `1px solid ${smeta.border}`,
            }}
          >
            {sentiment.replace("_", " ")}
          </span>
          <span style={{ fontSize: 12, color: "#8b949e", fontFamily: "var(--font-mono)" }}>
            ({items.length})
          </span>
        </div>

        {/* Avg relevance bar */}
        <div>
          <div style={{ width: "100%", height: 6, background: "#21262d", borderRadius: 999, overflow: "hidden", border: "1px solid #30363d" }}>
            <div style={{ height: "100%", width: `${avgRelevance * 100}%`, background: getBarFill(avgRelevance), borderRadius: 999 }} />
          </div>
        </div>

        {/* Avg % */}
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "#8b949e", textAlign: "right" }}>
          {(avgRelevance * 100).toFixed(0)}% avg
        </span>

        {/* Chevron — colour matches the relevance bar */}
        <span style={{
          color: avgRelevance >= 0.7 ? "#3fb950" : avgRelevance >= 0.4 ? "#d29922" : "#f85149",
          fontSize: 14,
          textAlign: "right",
          transition: "transform 0.2s ease",
          transform: expanded ? "rotate(90deg)" : "none",
          display: "block",
        }}>
          ›
        </span>
      </button>

      {/* Expanded items — always in DOM so @media print can reveal them */}
      <div
        className="source-items"
        style={{ borderTop: "1px solid #21262d", display: expanded ? "block" : "none" }}
      >
        {items.map((item, idx) => (
          <div
            key={idx}
            style={{
              padding: "12px 16px",
              borderBottom: idx < items.length - 1 ? "1px solid #21262d" : "none",
              background: "#0d1117",
            }}
          >
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12, marginBottom: 6 }}>
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  fontSize: 13, fontWeight: 600, color: "#58a6ff",
                  textDecoration: "none", lineHeight: 1.4, flex: 1,
                }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLAnchorElement).style.textDecoration = "underline"; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLAnchorElement).style.textDecoration = "none"; }}
              >
                {item.title} ↗
              </a>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "#8b949e", flexShrink: 0 }}>
                {(item.relevance_score * 100).toFixed(0)}%
              </span>
            </div>

            <p style={{ fontSize: 12, color: "#8b949e", lineHeight: 1.55, margin: "0 0 8px 0" }}>
              {item.summary}
            </p>

            {/* Per-item relevance bar */}
            <div style={{ display: "grid", gridTemplateColumns: "64px 1fr", gap: 8, alignItems: "center" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "#8b949e", letterSpacing: "0.06em" }}>
                RELEVANCE
              </span>
              <div style={{ height: 4, background: "#21262d", borderRadius: 999, overflow: "hidden", border: "1px solid #30363d" }}>
                <div style={{ height: "100%", width: `${item.relevance_score * 100}%`, background: getBarFill(item.relevance_score), borderRadius: 999 }} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
