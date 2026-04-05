import type { ReportVisual } from "@/lib/types";

export function ReportVisualBlock({ visual }: { visual: ReportVisual }) {
  if (!visual.points.length) {
    return null;
  }
  const maxValue = Math.max(...visual.points.map((point) => point.value), 1);

  return (
    <div className="rounded-2xl border border-border bg-muted/35 p-4">
      <p className="font-semibold">{visual.title}</p>
      {visual.description ? <p className="mt-1 text-sm text-muted-foreground">{visual.description}</p> : null}
      <div className="mt-4 space-y-3">
        {visual.points.map((point) => (
          <div key={point.label} className="space-y-1">
            <div className="flex items-center justify-between gap-3 text-sm">
              <span className="font-medium text-foreground">{point.label}</span>
              <span className="text-muted-foreground">
                {point.value}
                {visual.unit}
              </span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-white">
              <div
                className="h-full rounded-full bg-primary"
                style={{ width: `${Math.max(8, (point.value / maxValue) * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
