import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { fetchProviderSettings, updateProviderSettings } from "@/lib/api";
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

  const mutation = useMutation({
    mutationFn: async () =>
      updateProviderSettings({
        ...(openrouterKey ? { openrouter_api_key: openrouterKey } : {}),
        ...(tavilyKey ? { tavily_api_key: tavilyKey } : {}),
        persist: true,
      }),
    onSuccess: async () => {
      setMessage("Provider settings saved. Existing keys were preserved unless you entered a new one.");
      setOpenrouterKey("");
      setTavilyKey("");
      await refetch();
    },
    onError: (error) => {
      setMessage(error instanceof Error ? error.message : "Failed to save provider settings.");
    },
  });

  return (
    <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
      <Card>
        <CardHeader>
          <CardTitle>Provider configuration</CardTitle>
          <CardDescription>Save OpenRouter and Tavily keys for live LLM and web retrieval. arXiv remains enabled without a key.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="openrouter-key">OpenRouter API key</Label>
            <Input
              id="openrouter-key"
              type="password"
              placeholder="Paste a new OpenRouter key to update it"
              value={openrouterKey}
              onChange={(event) => setOpenrouterKey(event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="tavily-key">Tavily API key</Label>
            <Input
              id="tavily-key"
              type="password"
              placeholder="Paste a new Tavily key to update it"
              value={tavilyKey}
              onChange={(event) => setTavilyKey(event.target.value)}
            />
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
              {mutation.isPending ? "Saving…" : "Save provider settings"}
            </Button>
            {message ? <p className="text-sm text-muted-foreground">{message}</p> : null}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Provider status</CardTitle>
          <CardDescription>Statuses are loaded from the backend. Saved secrets are never returned to the browser.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading || !data ? (
            <p className="text-sm text-muted-foreground">Loading provider status…</p>
          ) : (
            <>
              <ProviderStatusRow name="OpenRouter" status={data.openrouter.status} detail={data.openrouter.model ?? "Model not set"} />
              <ProviderStatusRow name="Tavily" status={data.tavily.status} detail="Web and news retrieval" />
              <ProviderStatusRow name="arXiv" status={data.arxiv.status} detail={data.arxiv.note ?? "Academic retrieval"} />
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function ProviderStatusRow({ name, status, detail }: { name: string; status: string; detail: string }) {
  return (
    <div className="rounded-2xl border border-border bg-white/70 p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="font-semibold">{name}</p>
          <p className="text-sm text-muted-foreground">{detail}</p>
        </div>
        <Badge variant={status === "configured" || status === "enabled" ? "success" : "warning"}>{status}</Badge>
      </div>
    </div>
  );
}
