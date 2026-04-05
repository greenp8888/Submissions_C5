import type { ResearchSession } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export function TracePanel({
  session,
  activeFilter,
  onFilterChange,
}: {
  session: ResearchSession;
  activeFilter: string;
  onFilterChange: (value: string) => void;
}) {
  const traceRows = session.agent_trace.filter((trace) => !activeFilter || trace.agent.toLowerCase().includes(activeFilter.toLowerCase()) || trace.step.toLowerCase().includes(activeFilter.toLowerCase()));
  return (
    <Card>
      <CardHeader>
        <CardTitle>Agent trace</CardTitle>
        <CardDescription>Inspect the sequence of planner, retriever, analysis, insight, and reporting steps for this run.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-4 max-w-sm">
          <Input value={activeFilter} onChange={(event) => onFilterChange(event.target.value)} placeholder="Filter by agent or step" />
        </div>
        <div className="space-y-3">
          {traceRows.length === 0 ? (
            <p className="text-sm text-muted-foreground">No trace entries yet.</p>
          ) : (
            traceRows.map((trace) => (
              <div key={trace.id} className="rounded-2xl border border-border bg-white/75 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="secondary">{trace.agent}</Badge>
                  <Badge variant="muted">{trace.step}</Badge>
                  {trace.token_estimate ? <Badge variant="muted">{trace.token_estimate} tokens</Badge> : null}
                </div>
                {trace.input_summary ? <p className="mt-3 text-sm"><span className="font-semibold">Input:</span> {trace.input_summary}</p> : null}
                {trace.output_summary ? <p className="mt-2 text-sm text-muted-foreground"><span className="font-semibold text-foreground">Output:</span> {trace.output_summary}</p> : null}
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
