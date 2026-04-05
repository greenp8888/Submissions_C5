import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { fetchProviderSettings, updateProviderSettings } from "@/lib/api";
import { clearCachedProviderSettings, loadCachedProviderSettings, saveCachedProviderSettings } from "@/lib/browser-provider-settings";
import type { ProviderStatusEntry } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function ProviderSettingsForm() {
  const { data, refetch, isLoading } = useQuery({
    queryKey: ["provider-settings"],
    queryFn: fetchProviderSettings,
  });

  const [openrouterKey, setOpenrouterKey] = useState("");
  const [tavilyKey, setTavilyKey] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const cached = loadCachedProviderSettings();
    setOpenrouterKey(cached.openrouter_api_key);
    setTavilyKey(cached.tavily_api_key);
  }, []);

  const mutation = useMutation({
    mutationFn: async () =>
      updateProviderSettings({
        openrouter_api_key: openrouterKey.trim(),
        tavily_api_key: tavilyKey.trim(),
        persist: false,
      }),
    onSuccess: async () => {
      saveCachedProviderSettings({
        openrouter_api_key: openrouterKey.trim(),
        tavily_api_key: tavilyKey.trim(),
      });
      setMessage("Provider settings were saved to this browser and synced into the current backend runtime.");
      await refetch();
    },
    onError: (error) => {
      setMessage(error instanceof Error ? error.message : "Failed to save provider settings.");
    },
  });

  const handleClear = async () => {
    clearCachedProviderSettings();
    setOpenrouterKey("");
    setTavilyKey("");
    await updateProviderSettings({
      openrouter_api_key: "",
      tavily_api_key: "",
      persist: false,
    });
    setMessage("Provider settings were cleared from this browser and removed from the current backend runtime.");
    await refetch();
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
      <Card className="border-border bg-white/90">
        <CardHeader>
          <CardTitle>Provider settings</CardTitle>
          <CardDescription>
            Enter provider keys during first launch, keep them cached in this browser, and sync them into the active runtime session without writing them to <code>.env</code>.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="rounded-2xl border border-sky-200 bg-sky-50 p-4 text-sm text-slate-700">
            The backend starts without provider keys. This page is now the primary launch-time setup flow for OpenRouter and Tavily.
          </div>

          <div className="space-y-2">
            <Label htmlFor="openrouter-key">OpenRouter API key</Label>
            <Input
              id="openrouter-key"
              type="password"
              placeholder="Enter your OpenRouter key"
              value={openrouterKey}
              onChange={(event) => setOpenrouterKey(event.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="tavily-key">Tavily API key</Label>
            <Input
              id="tavily-key"
              type="password"
              placeholder="Enter your Tavily key"
              value={tavilyKey}
              onChange={(event) => setTavilyKey(event.target.value)}
            />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
              {mutation.isPending ? "Saving..." : "Save to browser and runtime"}
            </Button>
            <Button type="button" variant="outline" onClick={handleClear}>
              Clear cached keys
            </Button>
          </div>

          {message ? <p className="text-sm text-muted-foreground">{message}</p> : null}
        </CardContent>
      </Card>

      <Card className="border-border bg-white/90">
        <CardHeader>
          <CardTitle>Runtime provider status</CardTitle>
          <CardDescription>These statuses reflect the current backend runtime. Keys are never returned to the browser.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading || !data ? (
            <p className="text-sm text-muted-foreground">Loading provider status...</p>
          ) : (
            <>
              <ProviderStatusRow entry={data.openrouter} name="OpenRouter" detail={data.openrouter.model ?? "Model not set"} />
              <ProviderStatusRow entry={data.tavily} name="Tavily" detail={data.tavily.note ?? "Web and news retrieval"} />
              <ProviderStatusRow entry={data.arxiv} name="arXiv" detail={data.arxiv.note ?? "Academic retrieval"} />
            </>
          )}
        </CardContent>
      </Card>

      <Card className="border-border bg-white/90 xl:col-span-2">
        <CardHeader>
          <CardTitle>Model and provider usage detail</CardTitle>
          <CardDescription>
            See which model is active, which agents use it, and what each provider contributes to the research workflow.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-5 lg:grid-cols-3">
          {data ? (
            <>
              <ProviderDetailCard
                name="OpenRouter"
                eyebrow={data.openrouter.model ? `Model: ${data.openrouter.model}` : "Model not configured"}
                entry={data.openrouter}
              />
              <ProviderDetailCard name="Tavily" eyebrow="Web and news retrieval" entry={data.tavily} />
              <ProviderDetailCard name="arXiv" eyebrow="Academic paper retrieval" entry={data.arxiv} />
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Usage details will appear after provider status loads.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function ProviderStatusRow({ entry, name, detail }: { entry: ProviderStatusEntry; name: string; detail: string }) {
  return (
    <div className="rounded-2xl border border-border bg-slate-50 p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <p className="font-semibold text-slate-900">{name}</p>
          <p className="text-sm text-slate-600">{detail}</p>
          {entry.runtime_source ? <p className="text-xs text-slate-500">{entry.runtime_source}</p> : null}
        </div>
        <Badge variant={entry.status === "configured" || entry.status === "enabled" ? "success" : "warning"}>{entry.status}</Badge>
      </div>
    </div>
  );
}

function ProviderDetailCard({ name, eyebrow, entry }: { name: string; eyebrow: string; entry: ProviderStatusEntry }) {
  return (
    <div className="rounded-3xl border border-border bg-slate-50 p-5">
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">{eyebrow}</p>
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-lg font-semibold text-slate-900">{name}</h3>
          <Badge variant={entry.status === "configured" || entry.status === "enabled" ? "success" : "warning"}>{entry.status}</Badge>
        </div>
        {entry.note ? <p className="text-sm text-slate-600">{entry.note}</p> : null}
      </div>

      <div className="mt-5 space-y-3">
        {(entry.usages ?? []).map((usage) => (
          <div key={`${name}-${usage.agent}`} className="rounded-2xl border border-border bg-white p-4">
            <p className="font-medium text-slate-900">{usage.agent}</p>
            <p className="mt-1 text-sm text-slate-700">{usage.purpose}</p>
            <p className="mt-2 text-xs text-slate-500">
              Output: <span className="text-slate-700">{usage.output}</span>
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Fallback: <span className="text-slate-700">{usage.fallback}</span>
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
