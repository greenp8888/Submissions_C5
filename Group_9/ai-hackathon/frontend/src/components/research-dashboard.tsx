import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowUpRight, BookOpen, CalendarRange, CheckCircle2, Download, LoaderCircle, SearchCheck, Settings2, Sparkles } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { ConfidencePanel } from "@/components/confidence-panel";
import { GraphView } from "@/components/graph-view";
import { ProgressPanel } from "@/components/progress-panel";
import { ReferencesPanel } from "@/components/references-panel";
import { ReportPanel } from "@/components/report-panel";
import { TracePanel } from "@/components/trace-panel";
import { useResearchStream } from "@/hooks/use-research-stream";
import { digDeeper, exportUrl, fetchCollections, fetchProviderSettings, fetchSession, startResearch } from "@/lib/api";
import { DATE_PRESETS, presetToRange } from "@/lib/date-presets";
import type { ResearchFormValues, ResearchSession, Source, SourceChannel } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";

const defaultValues: ResearchFormValues = {
  query: "",
  batchTopics: "",
  runMode: "single",
  depth: "standard",
  enabledSources: ["local_rag", "web", "arxiv"],
  startDate: "",
  endDate: "",
  datePreset: "all_time",
  collectionIds: [],
  files: [],
};

export function ResearchDashboard({ sessionId }: { sessionId?: string }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [formValues, setFormValues] = useState<ResearchFormValues>(defaultValues);
  const [clientError, setClientError] = useState<string | null>(null);
  const [digDeeperTarget, setDigDeeperTarget] = useState("");

  const collectionsQuery = useQuery({ queryKey: ["collections"], queryFn: fetchCollections });
  const settingsQuery = useQuery({ queryKey: ["provider-settings"], queryFn: fetchProviderSettings });
  const sessionQuery = useQuery({
    queryKey: ["session", sessionId],
    queryFn: () => fetchSession(sessionId!),
    enabled: Boolean(sessionId),
    refetchOnWindowFocus: false,
  });

  const session = sessionQuery.data;
  const { streamState, lastEventType } = useResearchStream(sessionId, session?.status === "running");

  useEffect(() => {
    if (!session) {
      return;
    }
    setFormValues({
      query: session.run_mode === "batch" ? "" : session.query,
      batchTopics: session.batch_topics.join("\n"),
      runMode: session.run_mode,
      depth: session.depth,
      enabledSources: session.enabled_sources,
      startDate: session.start_date ?? "",
      endDate: session.end_date ?? "",
      datePreset: session.date_preset,
      collectionIds: session.selected_collection_ids,
      files: [],
    });
  }, [session]);

  const startMutation = useMutation({
    mutationFn: () => startResearch(formValues),
    onSuccess: (result) => {
      setClientError(null);
      navigate(`/sessions/${result.session_id}`);
    },
    onError: (error) => {
      setClientError(error instanceof Error ? error.message : "Failed to start research.");
    },
  });

  const digDeeperMutation = useMutation({
    mutationFn: async () => {
      if (!sessionId || !digDeeperTarget) {
        return;
      }
      const [kind, targetId] = digDeeperTarget.split(":", 2);
      await digDeeper(sessionId, {
        ...(kind === "finding" ? { finding_id: targetId } : {}),
        ...(kind === "claim" ? { claim_id: targetId } : {}),
        ...(kind === "insight" ? { insight_id: targetId } : {}),
      });
      await queryClient.invalidateQueries({ queryKey: ["session", sessionId] });
    },
    onError: (error) => {
      setClientError(error instanceof Error ? error.message : "Dig deeper failed.");
    },
  });

  const groupedSources = useMemo(() => groupSources(session?.sources ?? []), [session?.sources]);
  const targetOptions = useMemo(() => buildDigDeeperOptions(session), [session]);

  const handlePresetChange = (preset: ResearchFormValues["datePreset"]) => {
    const range = presetToRange(preset);
    setFormValues((current) => ({ ...current, datePreset: preset, startDate: range.startDate, endDate: range.endDate }));
  };

  const toggleSource = (source: SourceChannel, checked: boolean) => {
    setFormValues((current) => ({
      ...current,
      enabledSources: checked
        ? Array.from(new Set([...current.enabledSources, source]))
        : current.enabledSources.filter((value) => value !== source),
    }));
  };

  const handleRun = () => {
    const error = validateForm(formValues);
    setClientError(error);
    if (!error) {
      startMutation.mutate();
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-6 2xl:grid-cols-[420px_minmax(0,1fr)]">
        <Card className="h-fit">
          <CardHeader>
            <CardTitle>Research setup</CardTitle>
            <CardDescription>Choose the investigation mode, source mix, date window, collections, and uploads before running the graph.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="query">Research question</Label>
              <Textarea
                id="query"
                value={formValues.query}
                onChange={(event) => setFormValues((current) => ({ ...current, query: event.target.value }))}
                placeholder="What are the most promising approaches to solid-state battery commercialization, and where does the evidence disagree?"
                className="min-h-[132px]"
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <FieldSelect
                id="run-mode"
                label="Run mode"
                value={formValues.runMode}
                onChange={(value) => setFormValues((current) => ({ ...current, runMode: value as ResearchFormValues["runMode"] }))}
                options={[
                  ["single", "Single investigation"],
                  ["batch", "Batch topics"],
                ]}
              />
              <FieldSelect
                id="depth"
                label="Depth"
                value={formValues.depth}
                onChange={(value) => setFormValues((current) => ({ ...current, depth: value as ResearchFormValues["depth"] }))}
                options={[
                  ["quick", "Quick"],
                  ["standard", "Standard"],
                  ["deep", "Deep"],
                ]}
              />
            </div>

            {formValues.runMode === "batch" ? (
              <div className="space-y-2">
                <Label htmlFor="batch-topics">Batch topics</Label>
                <Textarea
                  id="batch-topics"
                  value={formValues.batchTopics}
                  onChange={(event) => setFormValues((current) => ({ ...current, batchTopics: event.target.value }))}
                  placeholder="One topic per line"
                  className="min-h-[120px]"
                />
              </div>
            ) : null}

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Sources</Label>
                <Link to="/settings" className="inline-flex items-center gap-1 text-xs font-semibold text-primary">
                  Provider settings <Settings2 className="h-3.5 w-3.5" />
                </Link>
              </div>
              {SOURCE_OPTIONS.map((item) => {
                const checked = formValues.enabledSources.includes(item.key);
                return (
                  <label key={item.key} className="flex cursor-pointer items-start gap-3 rounded-2xl border border-border bg-white/75 p-3">
                    <Checkbox checked={checked} onCheckedChange={(value) => toggleSource(item.key, Boolean(value))} />
                    <span>
                      <span className="block font-semibold">{item.label}</span>
                      <span className="block text-sm text-muted-foreground">{item.detail}</span>
                    </span>
                  </label>
                );
              })}
              <div className="flex flex-wrap gap-2">
                <ProviderHealthBadge label="OpenRouter" configured={settingsQuery.data?.openrouter.configured ?? false} />
                <ProviderHealthBadge label="Tavily" configured={settingsQuery.data?.tavily.configured ?? false} />
                <ProviderHealthBadge label="arXiv" configured />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <FieldSelect
                id="date-preset"
                label="Quick date preset"
                value={formValues.datePreset}
                onChange={(value) => handlePresetChange(value as ResearchFormValues["datePreset"])}
                options={DATE_PRESETS.map((preset) => [preset.value, preset.label])}
              />
              <div className="space-y-2">
                <Label htmlFor="collections">Collections</Label>
                <select
                  id="collections"
                  multiple
                  className="min-h-[90px] w-full rounded-xl border border-border bg-white/80 px-3 py-2 text-sm"
                  value={formValues.collectionIds}
                  onChange={(event) =>
                    setFormValues((current) => ({
                      ...current,
                      collectionIds: Array.from(event.target.selectedOptions).map((option) => option.value),
                    }))
                  }
                >
                  {(collectionsQuery.data?.collections ?? []).map((collection) => (
                    <option key={collection.id} value={collection.id}>
                      {collection.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <DateField id="start-date" label="Start date" value={formValues.startDate} onChange={(value) => setFormValues((current) => ({ ...current, startDate: value }))} />
              <DateField id="end-date" label="End date" value={formValues.endDate} onChange={(value) => setFormValues((current) => ({ ...current, endDate: value }))} />
            </div>

            <div className="space-y-2">
              <Label htmlFor="uploads">Upload files for this run</Label>
              <Input
                id="uploads"
                type="file"
                multiple
                accept=".pdf,.txt,.md"
                onChange={(event) => setFormValues((current) => ({ ...current, files: Array.from(event.target.files ?? []) }))}
              />
              {formValues.files.length ? (
                <div className="rounded-xl bg-muted/70 p-3 text-sm text-muted-foreground">{formValues.files.map((file) => file.name).join(", ")}</div>
              ) : null}
              <Link to="/knowledge" className="inline-flex items-center gap-1 text-xs font-semibold text-primary">
                Manage collections <ArrowUpRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            {clientError ? <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">{clientError}</div> : null}

            <div className="flex flex-wrap items-center gap-3">
              <Button onClick={handleRun} disabled={startMutation.isPending}>
                {startMutation.isPending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <SearchCheck className="h-4 w-4" />}
                {startMutation.isPending ? "Launching research…" : "Start research"}
              </Button>
              {sessionId ? <Badge variant="muted">Session {sessionId}</Badge> : null}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Status" value={session?.status ?? "idle"} icon={CheckCircle2} accent="success" />
            <MetricCard label="Sources" value={String(session?.sources.length ?? 0)} icon={BookOpen} />
            <MetricCard label="Claims" value={String(session?.claims.length ?? 0)} icon={Sparkles} />
            <MetricCard label="Date window" value={renderDateWindow(formValues.startDate, formValues.endDate)} icon={CalendarRange} />
          </div>

          {session ? (
            <>
              <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0">
                    <div>
                      <CardTitle>Research report</CardTitle>
                      <CardDescription>Long-form synthesis with methodology, evidence, credibility, contradictions, and references.</CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={session.status === "complete" ? "success" : session.status === "error" ? "warning" : "secondary"}>{session.status}</Badge>
                      <Badge variant={streamState === "live" ? "success" : "muted"}>{streamState}</Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <ReportPanel session={session} />
                  </CardContent>
                </Card>

                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Live research progress</CardTitle>
                      <CardDescription>Planner, retriever, analysis, and reporting events stream here while the session runs.</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ProgressPanel events={session.events} streamState={streamState} lastEventType={lastEventType} />
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Dig deeper</CardTitle>
                      <CardDescription>Open a focused sub-investigation from any finding, claim, or insight in the current session.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <select className="h-10 w-full rounded-xl border border-border bg-white/80 px-3 text-sm" value={digDeeperTarget} onChange={(event) => setDigDeeperTarget(event.target.value)}>
                        <option value="">Choose a finding, claim, or insight</option>
                        {targetOptions.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                      <div className="flex flex-wrap gap-3">
                        <Button onClick={() => digDeeperMutation.mutate()} disabled={!digDeeperTarget || digDeeperMutation.isPending}>
                          {digDeeperMutation.isPending ? "Running follow-up…" : "Investigate further"}
                        </Button>
                        <Button variant="outline" onClick={() => window.open(exportUrl(session.session_id, "markdown"), "_blank")}>
                          <Download className="h-4 w-4" />
                          Markdown
                        </Button>
                        <Button variant="outline" onClick={() => window.open(exportUrl(session.session_id, "pdf"), "_blank")}>
                          <Download className="h-4 w-4" />
                          PDF
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>

              <Tabs defaultValue="references">
                <TabsList>
                  <TabsTrigger value="references">References</TabsTrigger>
                  <TabsTrigger value="confidence">Confidence</TabsTrigger>
                  <TabsTrigger value="graph">Graph</TabsTrigger>
                  <TabsTrigger value="trace">Trace</TabsTrigger>
                </TabsList>
                <TabsContent value="references">
                  <ReferencesPanel groupedSources={groupedSources} />
                </TabsContent>
                <TabsContent value="confidence">
                  <ConfidencePanel claims={session.claims} />
                </TabsContent>
                <TabsContent value="graph">
                  <GraphView entities={session.entities} relationships={session.relationships} />
                </TabsContent>
                <TabsContent value="trace">
                  <TracePanel session={session} />
                </TabsContent>
              </Tabs>
            </>
          ) : (
            <Card>
              <CardContent className="p-8">
                <div className="flex flex-col items-start gap-4">
                  <Badge variant="secondary">Research workspace</Badge>
                  <h2 className="text-2xl">Start a session to populate the dashboard</h2>
                  <p className="max-w-3xl text-muted-foreground">
                    The new frontend is route-driven. Once you launch a run, you will land on a session URL with live progress, citations, graph, trace, and export actions connected to the FastAPI backend.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function FieldSelect({
  id,
  label,
  value,
  onChange,
  options,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<[string, string]>;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <select id={id} className="h-10 w-full rounded-xl border border-border bg-white/80 px-3 text-sm" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map(([optionValue, optionLabel]) => (
          <option key={optionValue} value={optionValue}>
            {optionLabel}
          </option>
        ))}
      </select>
    </div>
  );
}

function DateField({ id, label, value, onChange }: { id: string; label: string; value: string; onChange: (value: string) => void }) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <Input id={id} type="date" value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function ProviderHealthBadge({ label, configured }: { label: string; configured: boolean }) {
  return <Badge variant={configured ? "success" : "warning"}>{label}: {configured ? "ready" : "needs key"}</Badge>;
}

function MetricCard({
  label,
  value,
  icon: Icon,
  accent = "default",
}: {
  label: string;
  value: string;
  icon: typeof LoaderCircle;
  accent?: "default" | "success";
}) {
  return (
    <Card className={cn(accent === "success" && "border-emerald-200 bg-emerald-50/80")}>
      <CardContent className="flex items-center justify-between p-5">
        <div>
          <p className="subtle-label">{label}</p>
          <p className="mt-2 font-heading text-2xl capitalize">{value}</p>
        </div>
        <div className="rounded-2xl bg-white/75 p-3 text-primary">
          <Icon className="h-5 w-5" />
        </div>
      </CardContent>
    </Card>
  );
}

function validateForm(values: ResearchFormValues) {
  if (values.enabledSources.length === 0) {
    return "Select at least one source.";
  }
  if (values.startDate && values.endDate && values.startDate > values.endDate) {
    return "Start date must be on or before end date.";
  }
  if (values.runMode === "single" && !values.query.trim()) {
    return "A research question is required in single mode.";
  }
  if (values.runMode === "batch" && values.batchTopics.split(/\r?\n/).map((line) => line.trim()).filter(Boolean).length === 0) {
    return "At least one batch topic is required in batch mode.";
  }
  return null;
}

function buildDigDeeperOptions(session?: ResearchSession) {
  if (!session) {
    return [];
  }
  return [
    ...session.findings.slice(0, 12).map((finding) => ({ value: `finding:${finding.id}`, label: `Finding • ${finding.content.slice(0, 90)}` })),
    ...session.claims.slice(0, 12).map((claim) => ({ value: `claim:${claim.id}`, label: `Claim • ${claim.statement.slice(0, 90)}` })),
    ...session.insights.slice(0, 12).map((insight) => ({ value: `insight:${insight.id}`, label: `Insight • ${insight.label.slice(0, 90)}` })),
  ];
}

function groupSources(sources: Source[]) {
  return {
    "Local RAG": sources.filter((source) => source.provider === "local_rag"),
    Web: sources.filter((source) => source.provider === "tavily" && source.source_type === "web"),
    News: sources.filter((source) => source.provider === "tavily" && source.source_type === "news"),
    arXiv: sources.filter((source) => source.provider === "arxiv"),
  };
}

function renderDateWindow(startDate: string, endDate: string) {
  if (!startDate && !endDate) {
    return "All time";
  }
  return `${startDate || "Any"} → ${endDate || "Now"}`;
}

const SOURCE_OPTIONS: Array<{ key: SourceChannel; label: string; detail: string }> = [
  { key: "local_rag", label: "Local RAG", detail: "Search uploaded and indexed collections first." },
  { key: "web", label: "Web / Tavily", detail: "Enrich with web and news evidence when local support is incomplete." },
  { key: "arxiv", label: "arXiv", detail: "Add academic papers and publication metadata." },
];
