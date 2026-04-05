interface StreamingProgressProps {
  currentNode: string;
}

const nodes = [
  { id: "input",        label: "Input" },
  { id: "query_builder",label: "Queries" },
  { id: "retrieval",    label: "Retrieval" },
  { id: "matcher",      label: "Matching" },
  { id: "aggregator",   label: "Aggregating" },
  { id: "analysis",     label: "Analysis" },
  { id: "report",       label: "Report" },
];

export default function StreamingProgress({ currentNode }: StreamingProgressProps) {
  const currentIndex = nodes.findIndex((n) => n.id === currentNode);

  return (
    <div
      className="flex items-center gap-0 overflow-x-auto"
      role="status"
      aria-label="Analysis in progress"
    >
      {nodes.map((node, idx) => {
        const isActive    = idx === currentIndex;
        const isCompleted = idx < currentIndex;

        return (
          <div key={node.id} className="flex items-center">
            {idx > 0 && (
              <div
                style={{
                  width: 24,
                  height: 1,
                  background: isCompleted
                    ? "color-mix(in srgb, var(--accent-cyan) 45%, transparent)"
                    : "var(--rp-stream-line)",
                  flexShrink: 0,
                }}
              />
            )}
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-full"
              style={{
                background: isActive
                  ? "color-mix(in srgb, var(--accent-cyan) 14%, transparent)"
                  : isCompleted
                  ? "color-mix(in srgb, var(--accent-cyan) 7%, transparent)"
                  : "transparent",
                border: isActive
                  ? "1px solid color-mix(in srgb, var(--accent-cyan) 35%, transparent)"
                  : "1px solid transparent",
                flexShrink: 0,
              }}
            >
              <div
                className="rounded-full flex-shrink-0"
                style={{
                  width: 6,
                  height: 6,
                  background: isActive
                    ? "var(--accent-cyan)"
                    : isCompleted
                    ? "color-mix(in srgb, var(--accent-cyan) 45%, transparent)"
                    : "var(--rp-stream-dot-off)",
                  boxShadow: isActive ? "0 0 8px var(--accent-cyan)" : "none",
                  animation: isActive ? "glowPulse 1.5s ease-in-out infinite" : "none",
                }}
              />
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  letterSpacing: "0.04em",
                  color: isActive
                    ? "var(--accent-cyan)"
                    : isCompleted
                    ? "var(--rp-stream-text-mid)"
                    : "var(--rp-stream-text-dim)",
                  fontWeight: isActive ? 600 : 400,
                  whiteSpace: "nowrap",
                }}
              >
                {node.label}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
