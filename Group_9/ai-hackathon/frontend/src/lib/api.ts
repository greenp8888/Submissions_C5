import type {
  CollectionDetailsResponse,
  CollectionListResponse,
  ProviderSettingsResponse,
  ResearchFormValues,
  ResearchSession,
} from "@/lib/types";

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchProviderSettings() {
  return apiRequest<ProviderSettingsResponse>("/api/settings/providers");
}

export async function updateProviderSettings(payload: {
  openrouter_api_key?: string;
  tavily_api_key?: string;
  persist?: boolean;
}) {
  return apiRequest<ProviderSettingsResponse>("/api/settings/providers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchCollections() {
  return apiRequest<CollectionListResponse>("/api/knowledge/collections");
}

export async function fetchCollectionDetails(collectionId: string) {
  return apiRequest<CollectionDetailsResponse>(`/api/knowledge/collections/${collectionId}`);
}

export async function uploadKnowledge(collectionName: string, files: File[]) {
  const form = new FormData();
  form.append("collection_name", collectionName);
  files.forEach((file) => form.append("files", file));
  return apiRequest<{ collection_id: string; document_ids: string[]; status: string }>(
    `/api/knowledge/upload?collection_name=${encodeURIComponent(collectionName)}`,
    {
      method: "POST",
      body: form,
    },
  );
}

export async function startResearch(values: ResearchFormValues) {
  const form = new FormData();
  form.append("query", values.query);
  form.append("depth", values.depth);
  form.append("collection_ids", JSON.stringify(values.collectionIds));
  form.append("use_local_corpus", String(values.enabledSources.includes("local_rag")));
  form.append("enabled_sources", JSON.stringify(values.enabledSources));
  form.append("start_date", values.startDate);
  form.append("end_date", values.endDate);
  form.append("date_preset", values.datePreset);
  form.append(
    "batch_topics",
    JSON.stringify(
      values.batchTopics
        .split(/\r?\n/)
        .map((topic) => topic.trim())
        .filter(Boolean),
    ),
  );
  form.append("run_mode", values.runMode);
  form.append("debate_enabled", String(values.debateEnabled));
  form.append("position_a", values.positionA);
  form.append("position_b", values.positionB);
  values.files.forEach((file) => form.append("files", file));
  return apiRequest<{ session_id: string; status: string }>("/api/research", {
    method: "POST",
    body: form,
  });
}

export async function fetchSession(sessionId: string) {
  return apiRequest<ResearchSession>(`/api/research/${sessionId}/state`);
}

export async function digDeeper(sessionId: string, payload: { finding_id?: string; claim_id?: string; insight_id?: string }) {
  return apiRequest<{ session_id: string }>(`/api/research/${sessionId}/dig-deeper`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function exportUrl(sessionId: string, format: "markdown" | "pdf") {
  return `/api/research/${sessionId}/export/${format}`;
}
