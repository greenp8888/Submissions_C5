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
                    ? "rgba(34,211,238,0.5)"
                    : "rgba(255,255,255,0.08)",
                  flexShrink: 0,
                }}
              />
            )}
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-full"
              style={{
                background: isActive
                  ? "rgba(34,211,238,0.12)"
                  : isCompleted
                  ? "rgba(34,211,238,0.06)"
                  : "transparent",
                border: isActive
                  ? "1px solid rgba(34,211,238,0.35)"
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
                    ? "#22d3ee"
                    : isCompleted
                    ? "rgba(34,211,238,0.5)"
                    : "rgba(255,255,255,0.15)",
                  boxShadow: isActive ? "0 0 8px #22d3ee" : "none",
                  animation: isActive ? "glowPulse 1.5s ease-in-out infinite" : "none",
                }}
              />
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  letterSpacing: "0.04em",
                  color: isActive
                    ? "#22d3ee"
                    : isCompleted
                    ? "rgba(226,232,240,0.5)"
                    : "rgba(226,232,240,0.2)",
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
