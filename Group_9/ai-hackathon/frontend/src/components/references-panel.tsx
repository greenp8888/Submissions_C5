import { ArrowUpRight } from "lucide-react";

import type { Source } from "@/lib/types";
import { formatDate, truncate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function ReferencesPanel({ groupedSources }: { groupedSources: Record<string, Source[]> }) {
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
                  <div key={source.id} className="rounded-2xl border border-border bg-white/75 p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="font-semibold">{source.filename || source.title}</p>
                        <p className="text-sm text-muted-foreground">
                          {source.provider} • {source.source_type} • credibility {source.credibility_score.toFixed(2)} • relevance {source.relevance_score.toFixed(2)}
                        </p>
                      </div>
                      {source.url ? (
                        <a href={source.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-sm font-semibold text-primary">
                          Open <ArrowUpRight className="h-4 w-4" />
                        </a>
                      ) : null}
                    </div>
                    <p className="mt-3 text-sm text-slate-700">{truncate(source.snippet || "No snippet available.", 260)}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {source.page_refs.length ? <Badge variant="secondary">Pages {source.page_refs.join(", ")}</Badge> : null}
                      {source.published_date ? <Badge variant="muted">{formatDate(source.published_date)}</Badge> : null}
                      {source.matched_time_window === false ? <Badge variant="warning">Outside selected range</Badge> : null}
                    </div>
                    {source.credibility_explanation ? <p className="mt-3 text-xs text-muted-foreground">{source.credibility_explanation}</p> : null}
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
