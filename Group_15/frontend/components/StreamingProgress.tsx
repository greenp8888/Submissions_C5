interface StreamingProgressProps {
  currentNode: string;
}

const nodes = [
  { id: "input", label: "Input" },
  { id: "query_builder", label: "Queries" },
  { id: "retrieval", label: "Retrieval" },
  { id: "matcher", label: "Matching" },
  { id: "aggregator", label: "Aggregating" },
  { id: "analysis", label: "Analysis" },
  { id: "report", label: "Report" },
];

export default function StreamingProgress({ currentNode }: StreamingProgressProps) {
  const currentIndex = nodes.findIndex((n) => n.id === currentNode);

  return (
    <div className="flex items-center gap-2 font-mono text-xs text-muted">
      {nodes.map((node, idx) => {
        const isActive = idx === currentIndex;
        const isCompleted = idx < currentIndex;

        return (
          <div key={node.id} className="flex items-center gap-2">
            {idx > 0 && <span>·</span>}
            <span
              className={
                isActive
                  ? "text-ink animate-pulse"
                  : isCompleted
                  ? "text-muted opacity-50"
                  : "text-muted opacity-30"
              }
            >
              {node.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
