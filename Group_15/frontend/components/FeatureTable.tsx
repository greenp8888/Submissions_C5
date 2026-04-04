interface Feature {
  feature: string;
  rationale: string;
  priority: "high" | "medium" | "low";
}

interface FeatureTableProps {
  features: Feature[];
}

export default function FeatureTable({ features }: FeatureTableProps) {
  const priorityColors = {
    high: "text-ink",
    medium: "text-muted",
    low: "text-border",
  };

  const priorityLabels = {
    high: "[HIGH]",
    medium: "[MED]",
    low: "[LOW]",
  };

  return (
    <div className="space-y-2">
      {features.map((item, idx) => (
        <div key={idx} className="border-t border-border pt-3">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="font-serif text-lg mb-1">{item.feature}</div>
              <div className="text-muted text-sm">{item.rationale}</div>
            </div>
            <div
              className={`font-mono text-xs ${priorityColors[item.priority]} whitespace-nowrap`}
            >
              {priorityLabels[item.priority]}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
