import { ArrowUpRight, CheckCircle2 } from "lucide-react";

import type { Source } from "@/lib/types";
import { formatDate, truncate } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function ReferencesPanel({
  groupedSources,
  selectedSourceId,
  onSelectSource,
}: {
  groupedSources: Record<string, Source[]>;
  selectedSourceId: string | null;
  onSelectSource: (sourceId: string | null) => void;
}) {
  const entries = Object.entries(groupedSources);
  return (
    <div className="grid gap-6 xl:grid-cols-2">
      {entries.map(([group, sources]) => (
        <Card key={group}>
          <CardHeader>
            <CardTitle>{group}</CardTitle>
            <CardDescription>{sources.length} sources ranked by relevance and credibility.</CardDescription>
          </CardHeader>
          <CardContent>
            {sources.length === 0 ? (
              <p className="text-sm text-muted-foreground">No sources collected in this category.</p>
            ) : (
              <div className="space-y-3">
                {sources.map((source) => (
                  <div
                    key={source.id}
                    role="button"
                    tabIndex={0}
                    onClick={() => onSelectSource(source.id)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        onSelectSource(source.id);
                      }
                    }}
                    className={`w-full rounded-2xl border border-border bg-white p-4 text-left ${selectedSourceId === source.id ? "ring-2 ring-primary/20" : ""}`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="font-semibold">{source.filename || source.title}</p>
                        {selectedSourceId === source.id ? <span className="mt-1 inline-flex items-center gap-1 text-xs text-primary"><CheckCircle2 className="h-3.5 w-3.5" /> Selected reference</span> : null}
                      </div>
                      {source.url ? (
                        <a href={source.url} target="_blank" rel="noreferrer" onClick={(event) => event.stopPropagation()} className="inline-flex items-center gap-1 text-sm font-semibold text-primary">
                          Open <ArrowUpRight className="h-4 w-4" />
                        </a>
                      ) : null}
                    </div>
                    <p className="mt-3 text-sm leading-6 text-slate-800">{truncate(source.snippet || "No snippet available.", 260)}</p>
                    <div className="mt-3 space-y-1 text-xs text-slate-500">
                      <p>
                        <span className="font-semibold">Reference:</span> {source.filename || source.title}
                      </p>
                      <p>
                        <span className="font-semibold">Provider:</span> {humanize(source.provider)} |{" "}
                        <span className="font-semibold">Type:</span> {humanize(source.source_type)} |{" "}
                        <span className="font-semibold">Credibility:</span> {source.credibility_score.toFixed(2)} |{" "}
                        <span className="font-semibold">Relevance:</span> {source.relevance_score.toFixed(2)}
                      </p>
                      {source.page_refs.length ? <p><span className="font-semibold">Pages:</span> {source.page_refs.join(", ")}</p> : null}
                      {source.published_date ? <p><span className="font-semibold">Published:</span> {formatDate(source.published_date)}</p> : null}
                      {source.matched_time_window === false ? <p>Outside selected date range.</p> : null}
                      {source.credibility_explanation ? <p><span className="font-semibold">Credibility rationale:</span> {source.credibility_explanation}</p> : null}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function humanize(value: string) {
  return value.replace(/_/g, " ").replace(/—|–/g, "-");
}
