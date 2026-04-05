import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowUpRight, BookOpen, CalendarRange, CheckCircle2, ChevronDown, ChevronUp, Download, LoaderCircle, Scale, SearchCheck, Sparkles } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { ComparativeAnalysis } from "@/components/comparative-analysis";
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
import { useResearchOutputStore } from "@/store/research-output-store";
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
  debateEnabled: false,
  positionA: "",
  positionB: "",
  depth: "standard",
  enabledSources: ["local_rag", "web", "arxiv"],
  startDate: "",
  endDate: "",
  datePreset: "all_time",
  collectionIds: [],
  files: [],
};

const DRAFT_STORAGE_PREFIX = "ai-hackathon-research-draft";

export function ResearchDashboard({ sessionId, viewMode = "output" }: { sessionId?: string; viewMode?: "setup" | "output" }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const cachedSnapshot = useResearchOutputStore((state) => (sessionId ? state.cachedSessions[sessionId] : undefined));
  const currentSessionId = useResearchOutputStore((state) => state.currentSessionId);
  const cacheSession = useResearchOutputStore((state) => state.cacheSession);
  const setCurrentSession = useResearchOutputStore((state) => state.setCurrentSession);
  const setActiveTab = useResearchOutputStore((state) => state.setActiveTab);
  const setSelectedSection = useResearchOutputStore((state) => state.setSelectedSection);
  const setSelectedSource = useResearchOutputStore((state) => state.setSelectedSource);
  const setSelectedNode = useResearchOutputStore((state) => state.setSelectedNode);
  const setTraceFilter = useResearchOutputStore((state) => state.setTraceFilter);
  const setProgressExpandedState = useResearchOutputStore((state) => state.setProgressExpanded);
  const toggleComparativeSection = useResearchOutputStore((state) => state.toggleComparativeSection);
  const setGraphViewport = useResearchOutputStore((state) => state.setGraphViewport);
  const outputUiState = useResearchOutputStore((state) => (sessionId ? state.uiBySession[sessionId] : undefined));
  const [formValues, setFormValues] = useState<ResearchFormValues>(() => loadDraft(sessionId));
  const [clientError, setClientError] = useState<string | null>(null);
  const [digDeeperTarget, setDigDeeperTarget] = useState("");
  const [setupCollapsed, setSetupCollapsed] = useState(false);

  const collectionsQuery = useQuery({ queryKey: ["collections"], queryFn: fetchCollections });
  const settingsQuery = useQuery({ queryKey: ["provider-settings"], queryFn: fetchProviderSettings });
  const sessionQuery = useQuery({
    queryKey: ["session", sessionId],
    queryFn: () => fetchSession(sessionId!),
    enabled: Boolean(sessionId),
    refetchOnWindowFocus: false,
    initialData: cachedSnapshot?.session,
  });

  const session = sessionQuery.data;
  const { streamState, lastEventType } = useResearchStream(sessionId, session?.status === "running");

  useEffect(() => {
    if (!sessionId) {
      setFormValues(loadDraft());
      return;
    }
    setFormValues(loadDraft(sessionId));
  }, [sessionId]);

  useEffect(() => {
    if (!session) {
      return;
    }
    setCurrentSession(session.session_id);
    cacheSession(session);
    const sessionDefaults: ResearchFormValues = {
      query: session.run_mode === "batch" ? "" : session.query,
      batchTopics: session.batch_topics.join("\n"),
      runMode: session.run_mode,
      debateEnabled: session.debate_mode,
      positionA: session.position_a ?? "",
      positionB: session.position_b ?? "",
      depth: session.depth,
      enabledSources: session.enabled_sources,
      startDate: session.start_date ?? "",
      endDate: session.end_date ?? "",
      datePreset: session.date_preset,
      collectionIds: session.selected_collection_ids,
      files: [],
    };
    setFormValues(mergeDraft(loadDraft(session.session_id), sessionDefaults));
  }, [cacheSession, session, setCurrentSession]);

  useEffect(() => {
    saveDraft(sessionId, formValues);
  }, [formValues, sessionId]);

  const startMutation = useMutation({
    mutationFn: () => startResearch(formValues),
    onSuccess: (result) => {
      setClientError(null);
      saveDraft(result.session_id, formValues);
      navigate(`/research/output/${result.session_id}`);
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

  const liveRun = session?.status === "running" || streamState === "live" || startMutation.isPending;

  useEffect(() => {
    if (liveRun && sessionId) {
      setProgressExpandedState(sessionId, false);
    }
  }, [liveRun, sessionId, setProgressExpandedState]);

  const groupedSources = useMemo(() => groupSources(session?.sources ?? []), [session?.sources]);
  const targetOptions = useMemo(() => buildDigDeeperOptions(session), [session]);
  const showSetup = viewMode === "setup";
  const showOutput = viewMode === "output";

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
      {showOutput && liveRun ? <LiveAgentBar session={session} streamState={streamState} lastEventType={lastEventType} /> : null}

      {showSetup ? <Card>
        <CardHeader className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <CardTitle>Research setup</CardTitle>
            <CardDescription>Keep setup compact while giving the report maximum room once a run is in motion.</CardDescription>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button variant="outline" onClick={() => setSetupCollapsed((value) => !value)}>
              {setupCollapsed ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
              {setupCollapsed ? "Expand setup" : "Minimize setup"}
            </Button>
            <Button onClick={handleRun} disabled={startMutation.isPending}>
              {startMutation.isPending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <SearchCheck className="h-4 w-4" />}
              {startMutation.isPending ? "Launching research..." : "Start research"}
            </Button>
            {sessionId ? <Badge variant="muted">Session {sessionId}</Badge> : null}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="query">Research question</Label>
            <Textarea
              id="query"
              value={formValues.query}
              onChange={(event) => setFormValues((current) => ({ ...current, query: event.target.value }))}
              placeholder="What are the most promising approaches to solid-state battery commercialization, and where does the evidence disagree?"
              className={cn("min-h-[180px]", setupCollapsed && "min-h-[120px]")}
            />
          </div>

          {!setupCollapsed ? (
            <>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
                <FieldSelect
                  id="run-mode"
                  label="Run mode"
                  value={formValues.runMode}
                  onChange={(value) =>
                    setFormValues((current) => ({
                      ...current,
                      runMode: value as ResearchFormValues["runMode"],
                      debateEnabled: value === "batch" ? false : current.debateEnabled,
                      positionA: value === "batch" ? "" : current.positionA,
                      positionB: value === "batch" ? "" : current.positionB,
                    }))
                  }
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
                <FieldSelect
                  id="date-preset"
                  label="Quick date preset"
                  value={formValues.datePreset}
                  onChange={(value) => handlePresetChange(value as ResearchFormValues["datePreset"])}
                  options={DATE_PRESETS.map((preset) => [preset.value, preset.label])}
                />
                <DateField id="start-date" label="Start date" value={formValues.startDate} onChange={(value) => setFormValues((current) => ({ ...current, startDate: value }))} />
                <DateField id="end-date" label="End date" value={formValues.endDate} onChange={(value) => setFormValues((current) => ({ ...current, endDate: value }))} />
              </div>

              {formValues.runMode === "batch" ? (
                <div className="space-y-2">
                  <Label htmlFor="batch-topics">Batch topics</Label>
                  <Textarea
                    id="batch-topics"
                    value={formValues.batchTopics}
                    onChange={(event) => setFormValues((current) => ({ ...current, batchTopics: event.target.value }))}
                    placeholder="One topic per line"
                    className="min-h-[110px]"
                  />
                </div>
              ) : null}

              <div className="grid gap-4 xl:grid-cols-[1.25fr_1fr_1.1fr]">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Sources</Label>
                    <Badge variant="muted">Configure from Settings</Badge>
                  </div>
                  <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-1">
                    {SOURCE_OPTIONS.map((item) => {
                      const checked = formValues.enabledSources.includes(item.key);
                      return (
                        <label key={item.key} className="flex cursor-pointer items-start gap-3 rounded-2xl border border-border bg-white p-3">
                          <Checkbox checked={checked} onCheckedChange={(value) => toggleSource(item.key, Boolean(value))} />
                          <span>
                            <span className="block font-semibold">{item.label}</span>
                            <span className="block text-sm text-muted-foreground">{item.detail}</span>
                          </span>
                        </label>
                      );
                    })}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <ProviderHealthBadge label="OpenRouter" configured={settingsQuery.data?.openrouter.configured ?? false} />
                    <ProviderHealthBadge label="Tavily" configured={settingsQuery.data?.tavily.configured ?? false} />
                    <ProviderHealthBadge label="arXiv" configured />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="collections">Collections</Label>
                  <select
                    id="collections"
                    multiple
                    className="min-h-[152px] w-full rounded-xl border border-border bg-white px-3 py-2 text-sm text-foreground"
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
                  <Link to="/knowledge" className="inline-flex items-center gap-1 text-xs font-semibold text-primary">
                    Open Research Documents <ArrowUpRight className="h-3.5 w-3.5" />
                  </Link>
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
                  <div className="rounded-2xl border border-border bg-slate-50 p-4">
                    <p className="text-sm font-semibold">Upload to RAG online knowledge building</p>
                    <p className="mt-1 text-sm text-muted-foreground">Attach PDFs, markdown, or text files here, or use the Research Documents page to build reusable collections.</p>
                    {formValues.files.length ? (
                      <div className="mt-3 rounded-xl bg-muted/70 p-3 text-sm text-muted-foreground">{formValues.files.map((file) => file.name).join(", ")}</div>
                    ) : (
                      <p className="mt-3 text-sm text-muted-foreground">No files selected for this run.</p>
                    )}
                  </div>
                </div>
              </div>

              {formValues.runMode === "single" ? (
                <div className="space-y-4 rounded-2xl border border-border bg-slate-50 p-4">
                  <label className="flex cursor-pointer items-start gap-3">
                    <Checkbox
                      checked={formValues.debateEnabled}
                      onCheckedChange={(value) =>
                        setFormValues((current) => ({
                          ...current,
                          debateEnabled: Boolean(value),
                          positionA: Boolean(value) ? current.positionA : "",
                          positionB: Boolean(value) ? current.positionB : "",
                        }))
                      }
                    />
                    <span>
                      <span className="flex items-center gap-2 font-semibold">
                        <Scale className="h-4 w-4" />
                        Debate mode
                      </span>
                      <span className="block text-sm text-muted-foreground">Compare two competing positions and merge the disagreements into one comparative analysis view.</span>
                    </span>
                  </label>
                  {formValues.debateEnabled ? (
                    <div className="grid gap-4 xl:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="position-a">Position A</Label>
                        <Textarea
                          id="position-a"
                          value={formValues.positionA}
                          onChange={(event) => setFormValues((current) => ({ ...current, positionA: event.target.value }))}
                          placeholder="Example: Solid-state batteries will achieve mass-market EV adoption within this decade."
                          className="min-h-[90px]"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="position-b">Position B</Label>
                        <Textarea
                          id="position-b"
                          value={formValues.positionB}
                          onChange={(event) => setFormValues((current) => ({ ...current, positionB: event.target.value }))}
                          placeholder="Example: Manufacturing, materials, and cost barriers will delay mass-market EV adoption beyond this decade."
                          className="min-h-[90px]"
                        />
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </>
          ) : (
            <div className="flex flex-wrap gap-2">
              {formValues.enabledSources.map((source) => (
                <Badge key={source} variant="secondary">{source}</Badge>
              ))}
              {formValues.collectionIds.length ? <Badge variant="muted">{formValues.collectionIds.length} collections selected</Badge> : null}
              {formValues.files.length ? <Badge variant="muted">{formValues.files.length} uploads attached</Badge> : null}
              {formValues.debateEnabled ? <Badge variant="warning">Debate mode enabled</Badge> : null}
            </div>
          )}

          {clientError ? <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">{clientError}</div> : null}
        </CardContent>
      </Card> : null}

      {showOutput ? <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Status" value={session?.status ?? "idle"} icon={CheckCircle2} accent="success" />
            <MetricCard label="Sources" value={String(session?.sources.length ?? 0)} icon={BookOpen} />
            <MetricCard label="Claims" value={String(session?.claims.length ?? 0)} icon={Sparkles} />
            <MetricCard label="Date window" value={renderDateWindow(formValues.startDate, formValues.endDate)} icon={CalendarRange} />
          </div>

          {session ? (
            <>
              <details
                className="panel-surface overflow-hidden"
                open={outputUiState?.progressExpanded ?? false}
                onToggle={(event) => sessionId && setProgressExpandedState(sessionId, (event.currentTarget as HTMLDetailsElement).open)}
              >
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4 p-5">
                  <div>
                    <p className="font-semibold">Live research progress</p>
                    <p className="text-sm text-muted-foreground">Keep this minimized while the report takes center stage, or expand it to inspect recent agent activity.</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={streamState === "live" ? "success" : "muted"}>{streamState}</Badge>
                    {lastEventType ? <Badge variant="secondary">{lastEventType}</Badge> : null}
                    {(outputUiState?.progressExpanded ?? false) ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </div>
                </summary>
                <div className="border-t border-border px-5 pb-5 pt-3">
                  <ProgressPanel events={session.events} streamState={streamState} lastEventType={lastEventType} />
                </div>
              </details>

              <Card>
                <CardHeader className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <CardTitle>Research report</CardTitle>
                    <CardDescription>Long-form synthesis with methodology, evidence, credibility, contradictions, and references.</CardDescription>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={session.status === "complete" ? "success" : session.status === "error" ? "warning" : "secondary"}>{session.status}</Badge>
                    <select className="h-10 min-w-[280px] rounded-xl border border-border bg-white px-3 text-sm text-foreground" value={digDeeperTarget} onChange={(event) => setDigDeeperTarget(event.target.value)}>
                      <option value="">Choose a finding, claim, or insight</option>
                      {targetOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                    <Button onClick={() => digDeeperMutation.mutate()} disabled={!digDeeperTarget || digDeeperMutation.isPending}>
                      {digDeeperMutation.isPending ? "Running follow-up..." : "Investigate further"}
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
                </CardHeader>
                <CardContent>
                  <ReportPanel
                    session={session}
                    selectedSectionId={outputUiState?.selectedSectionId ?? null}
                    onSelectSection={(sectionId) => sessionId && setSelectedSection(sessionId, sectionId)}
                  />
                </CardContent>
              </Card>

              <ComparativeAnalysis
                session={session}
                expandedSections={outputUiState?.expandedComparativeSections ?? []}
                onToggleSection={(section, expanded) => sessionId && toggleComparativeSection(sessionId, section, expanded)}
              />

              <Tabs
                value={outputUiState?.activeTab ?? "references"}
                onValueChange={(value) => sessionId && setActiveTab(sessionId, value as "references" | "confidence" | "graph" | "trace")}
              >
                <TabsList>
                  <TabsTrigger value="references">References</TabsTrigger>
                  <TabsTrigger value="confidence">Confidence</TabsTrigger>
                  <TabsTrigger value="graph">Graph</TabsTrigger>
                  <TabsTrigger value="trace">Trace</TabsTrigger>
                </TabsList>
                <TabsContent value="references">
                  <ReferencesPanel
                    groupedSources={groupedSources}
                    selectedSourceId={outputUiState?.selectedSourceId ?? null}
                    onSelectSource={(sourceId) => sessionId && setSelectedSource(sessionId, sourceId)}
                  />
                </TabsContent>
                <TabsContent value="confidence">
                  <ConfidencePanel claims={session.claims} />
                </TabsContent>
                <TabsContent value="graph">
                  <GraphView
                    entities={session.entities}
                    relationships={session.relationships}
                    selectedNodeId={outputUiState?.selectedNodeId ?? null}
                    viewport={outputUiState?.graphViewport ?? null}
                    onSelectNode={(nodeId) => sessionId && setSelectedNode(sessionId, nodeId)}
                    onViewportChange={(viewport) => sessionId && setGraphViewport(sessionId, viewport)}
                  />
                </TabsContent>
                <TabsContent value="trace">
                  <TracePanel
                    session={session}
                    activeFilter={outputUiState?.traceFilter ?? ""}
                    onFilterChange={(filter) => sessionId && setTraceFilter(sessionId, filter)}
                  />
                </TabsContent>
              </Tabs>
            </>
          ) : (
            <Card>
              <CardContent className="p-8">
                <div className="flex flex-col items-start gap-4">
                  <Badge variant="secondary">Research Output</Badge>
                  <h2 className="text-2xl">No active research output yet</h2>
                  <p className="max-w-3xl text-muted-foreground">
                    Start a run from Research Setup to populate this workspace with live progress, report sections, references, charts when explicit quantitative data exists, graph, and trace output.
                  </p>
                  <div className="flex flex-wrap gap-3">
                    <Button onClick={() => navigate("/research/setup")}>Go to Research Setup</Button>
                    {currentSessionId ? <Button variant="outline" onClick={() => navigate(`/research/output/${currentSessionId}`)}>Open last session</Button> : null}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
      </div> : null}
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
  if (values.runMode === "batch" && values.debateEnabled) {
    return "Debate mode is available only for single investigations.";
  }
  if (values.debateEnabled && (!values.positionA.trim() || !values.positionB.trim())) {
    return "Position A and Position B are required when debate mode is enabled.";
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

function draftStorageKey(sessionId?: string) {
  return `${DRAFT_STORAGE_PREFIX}:${sessionId ?? "new"}`;
}

function loadDraft(sessionId?: string): ResearchFormValues {
  if (typeof window === "undefined") {
    return defaultValues;
  }
  try {
    const raw = window.localStorage.getItem(draftStorageKey(sessionId));
    if (!raw) {
      return { ...defaultValues };
    }
    const parsed = JSON.parse(raw) as Partial<Omit<ResearchFormValues, "files">>;
    return mergeDraft(parsed, defaultValues);
  } catch {
    return { ...defaultValues };
  }
}

function saveDraft(sessionId: string | undefined, values: ResearchFormValues) {
  if (typeof window === "undefined") {
    return;
  }
  const payload: Omit<ResearchFormValues, "files"> = {
    query: values.query,
    batchTopics: values.batchTopics,
    runMode: values.runMode,
    debateEnabled: values.debateEnabled,
    positionA: values.positionA,
    positionB: values.positionB,
    depth: values.depth,
    enabledSources: values.enabledSources,
    startDate: values.startDate,
    endDate: values.endDate,
    datePreset: values.datePreset,
    collectionIds: values.collectionIds,
  };
  window.localStorage.setItem(draftStorageKey(sessionId), JSON.stringify(payload));
}

function mergeDraft(
  draft: Partial<Omit<ResearchFormValues, "files">>,
  base: ResearchFormValues,
): ResearchFormValues {
  return {
    ...base,
    ...draft,
    enabledSources: Array.isArray(draft.enabledSources) && draft.enabledSources.length ? draft.enabledSources : base.enabledSources,
    collectionIds: Array.isArray(draft.collectionIds) ? draft.collectionIds : base.collectionIds,
    files: [],
  };
}

function LiveAgentBar({
  session,
  streamState,
  lastEventType,
}: {
  session?: ResearchSession;
  streamState: string;
  lastEventType: string | null;
}) {
  const latestTrace = session?.agent_trace.at(-1);
  const recentEvents = session?.events.slice(-4).reverse() ?? [];
  const stages = ["planner", "retriever", "analysis", "insight", "reporter", "qa review"];
  const traceAgents = new Set((session?.agent_trace ?? []).map((trace) => trace.agent.replace(/_/g, " ")));
  const activeAgent = (latestTrace?.agent || recentEvents[0]?.agent || "coordinator").replace(/_/g, " ");

  return (
    <div className="panel-surface overflow-hidden">
      <div className="h-1.5 w-full overflow-hidden bg-slate-200">
        <div className="h-full w-1/3 animate-[pulse_1.8s_ease-in-out_infinite] rounded-full bg-primary" />
      </div>
      <div className="flex flex-col gap-3 p-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-3">
          <p className="subtle-label">Agent Trace Live View</p>
          <p className="font-semibold text-slate-900">Research is live right now</p>
          <p className="text-sm text-slate-600">
            {session?.events.length ? session.events[session.events.length - 1]?.message : "Agents are coordinating the current investigation."}
          </p>
          <div className="flex flex-wrap gap-2">
            {stages.map((stage) => (
              <Badge key={stage} variant={activeAgent === stage ? "success" : traceAgents.has(stage) ? "secondary" : "muted"}>
                {stage}
              </Badge>
            ))}
          </div>
          {latestTrace ? (
            <div className="rounded-2xl border border-border bg-slate-50 p-3">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Current operation</p>
              <p className="mt-2 text-sm font-semibold text-slate-900">
                {latestTrace.agent.replace(/_/g, " ")} • {latestTrace.step.replace(/_/g, " ")}
              </p>
              {latestTrace.output_summary ? <p className="mt-1 text-sm text-slate-600">{latestTrace.output_summary}</p> : null}
            </div>
          ) : null}
        </div>
        <div className="flex max-w-xl flex-col gap-3">
          <div className="flex flex-wrap items-center gap-2">
            {session ? <Badge variant="secondary">Status: {session.status}</Badge> : null}
            <Badge variant={streamState === "live" ? "success" : "secondary"}>{streamState}</Badge>
            {lastEventType ? <Badge variant="muted">Last: {lastEventType}</Badge> : null}
            {session ? <Badge variant="muted">{session.agent_trace.length} trace steps</Badge> : null}
          </div>
          <div className="space-y-2">
            {recentEvents.map((event, index) => (
              <div key={`${event.timestamp}-${index}`} className="rounded-2xl border border-border bg-white p-3">
                <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{(event.agent || event.event_type).replace(/_/g, " ")}</p>
                <p className="mt-1 text-sm text-slate-900">{event.message}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

const SOURCE_OPTIONS: Array<{ key: SourceChannel; label: string; detail: string }> = [
  { key: "local_rag", label: "Local RAG", detail: "Search uploaded and indexed collections first." },
  { key: "web", label: "Web / Tavily", detail: "Enrich with web and news evidence when local support is incomplete." },
  { key: "arxiv", label: "arXiv", detail: "Add academic papers and publication metadata." },
];
