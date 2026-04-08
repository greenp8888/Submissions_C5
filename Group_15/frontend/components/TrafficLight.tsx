interface TrafficLightProps {
  status: "green" | "amber" | "red";
  reason: string;
}

export default function TrafficLight({ status, reason }: TrafficLightProps) {
  const colors = {
    green: "bg-green",
    amber: "bg-amber",
    red: "bg-red",
  };

  const labels = {
    green: "Clear",
    amber: "Moderate",
    red: "Crowded",
  };

  return (
    <div className="flex items-center gap-3">
      <div className={`w-3 h-3 rounded-full ${colors[status]}`} />
      <span className="font-mono text-sm uppercase tracking-wide">{labels[status]}</span>
      <span className="text-muted text-sm">— {reason}</span>
    </div>
  );
}
