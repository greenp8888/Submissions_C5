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
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={streamState === "live" ? "success" : "muted"}>{streamState}</Badge>
        {lastEventType ? <Badge variant="secondary">Last event: {lastEventType}</Badge> : null}
      </div>
      <div className="max-h-[560px] space-y-3 overflow-auto pr-1">
        {events.length === 0 ? (
          <p className="text-sm text-muted-foreground">Waiting for research activity…</p>
        ) : (
          [...events].reverse().map((event, index) => (
            <div key={`${event.timestamp}-${index}`} className="rounded-2xl border border-border bg-white/75 p-4">
              <div className="flex items-center justify-between gap-3">
                <Badge variant="secondary">{event.event_type}</Badge>
                <span className="text-xs text-muted-foreground">{formatDate(event.timestamp)}</span>
              </div>
              <p className="mt-3 text-sm font-semibold">{event.message}</p>
              {event.agent ? <p className="mt-1 text-xs uppercase tracking-[0.15em] text-muted-foreground">{event.agent}</p> : null}
              {Object.keys(event.data).length ? (
                <div className="mt-3 space-y-1 text-xs text-muted-foreground">
                  {Object.entries(event.data).map(([key, value]) => (
                    <p key={key}>
                      <span className="font-semibold text-foreground">{key}:</span> {String(value)}
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
