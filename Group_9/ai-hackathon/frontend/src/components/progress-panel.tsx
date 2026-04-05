import type { ResearchEvent } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

export function ProgressPanel({
  events,
  streamState,
  lastEventType,
}: {
  events: ResearchEvent[];
  streamState: string;
  lastEventType: string | null;
}) {
  const latestByAgent = new Map<string, ResearchEvent>();
  for (const event of [...events].reverse()) {
    if (event.agent && !latestByAgent.has(event.agent)) {
      latestByAgent.set(event.agent, event);
    }
  }
  const agentRows = [...latestByAgent.entries()].slice(0, 6);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={streamState === "live" ? "success" : "muted"}>{streamState}</Badge>
        {lastEventType ? <Badge variant="secondary">Last event: {lastEventType}</Badge> : null}
      </div>
      {agentRows.length ? (
        <div className="grid gap-3 lg:grid-cols-3">
          {agentRows.map(([agent, event]) => (
            <div key={agent} className="rounded-2xl border border-border bg-slate-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{agent}</p>
              <p className="mt-2 font-semibold text-slate-900">{event.message}</p>
              <p className="mt-2 text-xs text-slate-500">{formatDate(event.timestamp)}</p>
            </div>
          ))}
        </div>
      ) : null}
      <div className="max-h-[560px] space-y-3 overflow-auto pr-1">
        {events.length === 0 ? (
          <p className="text-sm text-muted-foreground">Waiting for research activity...</p>
        ) : (
          [...events].reverse().map((event, index) => (
            <div key={`${event.timestamp}-${index}`} className="rounded-2xl border border-border bg-white p-4">
              <div className="flex items-center justify-between gap-3">
                <Badge variant="secondary">{event.event_type}</Badge>
                <span className="text-xs text-muted-foreground">{formatDate(event.timestamp)}</span>
              </div>
              <p className="mt-3 text-sm font-semibold text-slate-900">{event.message}</p>
              {event.agent ? <p className="mt-1 text-xs uppercase tracking-[0.15em] text-muted-foreground">{event.agent}</p> : null}
              {Object.keys(event.data).length ? (
                <div className="mt-3 space-y-1 text-xs text-muted-foreground">
                  {Object.entries(event.data).map(([key, value]) => (
                    <p key={key}>
                      <span className="font-semibold text-slate-700">{key}:</span> {String(value)}
                    </p>
                  ))}
                </div>
              ) : null}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
