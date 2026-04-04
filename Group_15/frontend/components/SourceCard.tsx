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

const sourceLabels: Record<string, string> = {
  github: "GitHub",
  reddit: "Reddit",
  hn: "Hacker News",
  ph: "Product Hunt",
  ai4that: "ThereIsAnAIForThat",
  yc: "Y Combinator",
};

const sentimentDots: Record<string, string> = {
  positive: "bg-green",
  neutral: "bg-muted",
  negative: "bg-red",
  insufficient_data: "bg-border",
};

export default function SourceCard({ source, items, sentiment }: SourceCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border-t border-border py-4">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between text-left hover:opacity-70 transition-opacity"
      >
        <div className="flex items-center gap-3">
          <div className={`w-2 h-2 rounded-full ${sentimentDots[sentiment] || sentimentDots.neutral}`} />
          <span className="font-mono text-sm uppercase tracking-wide">{sourceLabels[source]}</span>
          <span className="text-muted font-mono text-xs">({items.length})</span>
        </div>
        <span className="text-muted text-sm">{expanded ? "−" : "+"}</span>
      </button>

      {expanded && (
        <div className="mt-4 space-y-4">
          {items.map((item, idx) => (
            <div key={idx} className="pl-5">
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="font-serif text-base hover:underline"
              >
                {item.title}
              </a>
              <div className="text-muted text-sm mt-1">{item.summary}</div>
              <div className="mt-2 h-0.5 bg-border" style={{ width: `${item.relevance_score * 100}%` }} />
              <div className="font-mono text-xs text-muted mt-1">
                {(item.relevance_score * 100).toFixed(0)}% relevance
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
