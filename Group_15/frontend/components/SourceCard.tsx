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
      data-source-card
      style={{
        background: "var(--rp-card)",
        border: "1px solid var(--rp-border)",
        borderRadius: 14,
        overflow: "hidden",
        transition: "border-color 0.2s ease",
      }}
      onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "var(--rp-source-hover-border)"; }}
      onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "var(--rp-border)"; }}
    >
      {/* Header row */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="source-items-toggle w-full cursor-pointer"
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
            data-report-dot=""
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
              color: "var(--rp-heading)",
            }}
          >
            {SOURCE_LABELS[source] ?? source}
          </span>
          <span
            data-report-accent={true}
            style={{
              padding: "1px 7px", borderRadius: 999, fontSize: 10,
              fontWeight: 700, fontFamily: "var(--font-mono)",
              letterSpacing: "0.06em",
              background: smeta.bg, color: smeta.color, border: `1px solid ${smeta.border}`,
              ["--report-accent-color" as string]: smeta.color,
            }}
          >
            {sentiment.replace("_", " ")}
          </span>
          <span style={{ fontSize: 12, color: "var(--rp-muted)", fontFamily: "var(--font-mono)" }}>
            ({items.length})
          </span>
        </div>

        {/* Avg relevance bar */}
        <div>
          <div
            data-report-bar-track=""
            style={{ width: "100%", height: 6, background: "var(--rp-row)", borderRadius: 999, overflow: "hidden", border: "1px solid var(--rp-border)" }}
          >
            <div
              data-report-bar-fill=""
              style={{ height: "100%", width: `${avgRelevance * 100}%`, background: getBarFill(avgRelevance), borderRadius: 999 }}
            />
          </div>
        </div>

        {/* Avg % */}
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--rp-muted)", textAlign: "right" }}>
          {(avgRelevance * 100).toFixed(0)}% avg
        </span>

        {/* Chevron — colour matches the relevance bar */}
        <span
          className="source-chevron"
          data-report-accent={true}
          style={{
          color: avgRelevance >= 0.7 ? "#3fb950" : avgRelevance >= 0.4 ? "#d29922" : "#f85149",
          fontSize: 14,
          textAlign: "right",
          transition: "transform 0.2s ease",
          transform: expanded ? "rotate(90deg)" : "none",
          display: "block",
          ["--report-accent-color" as string]:
            avgRelevance >= 0.7 ? "#3fb950" : avgRelevance >= 0.4 ? "#d29922" : "#f85149",
        }}
        >
          ›
        </span>
      </button>

      {/* Expanded items — always in DOM so @media print can reveal them */}
      <div
        className="source-items"
        style={{ borderTop: "1px solid var(--rp-row)", display: expanded ? "block" : "none" }}
      >
        {items.map((item, idx) => (
          <div
            key={idx}
            style={{
              padding: "12px 16px",
              borderBottom: idx < items.length - 1 ? "1px solid var(--rp-row)" : "none",
              background: "var(--rp-inset)",
            }}
          >
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12, marginBottom: 6 }}>
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  fontSize: 13, fontWeight: 600, color: "var(--rp-link)",
                  textDecoration: "none", lineHeight: 1.4, flex: 1,
                }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLAnchorElement).style.textDecoration = "underline"; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLAnchorElement).style.textDecoration = "none"; }}
              >
                {item.title} ↗
              </a>
              <span
                data-report-accent={true}
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  color: "var(--rp-muted)",
                  flexShrink: 0,
                  ["--report-accent-color" as string]:
                    item.relevance_score >= 0.7
                      ? "#3fb950"
                      : item.relevance_score >= 0.4
                        ? "#d29922"
                        : "#f85149",
                }}
              >
                {(item.relevance_score * 100).toFixed(0)}%
              </span>
            </div>

            <p style={{ fontSize: 12, color: "var(--rp-muted)", lineHeight: 1.55, margin: "0 0 8px 0" }}>
              {item.summary}
            </p>

            {/* Per-item relevance bar */}
            <div style={{ display: "grid", gridTemplateColumns: "64px 1fr", gap: 8, alignItems: "center" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--rp-muted)", letterSpacing: "0.06em" }}>
                RELEVANCE
              </span>
              <div
                data-report-bar-track=""
                style={{ height: 4, background: "var(--rp-row)", borderRadius: 999, overflow: "hidden", border: "1px solid var(--rp-border)" }}
              >
                <div
                  data-report-bar-fill=""
                  style={{
                    height: "100%",
                    width: `${item.relevance_score * 100}%`,
                    background: getBarFill(item.relevance_score),
                    borderRadius: 999,
                  }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
