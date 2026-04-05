import { create } from "zustand";
import { persist } from "zustand/middleware";

// ── Default config values ─────────────────────────────────────────────────────
const DEFAULT_CONFIG = {
  openrouterKey: "",
  tavilyKey: "",
  model: "openai/gpt-4o-mini",
  temperature: 0.1,
  goals: "",
  brevoApiKey: "",
  brevoFromEmail: "",
};

export const useFinancialStore = create(
  persist(
    (set, get) => ({
      // ── Navigation ──────────────────────────────────────────────────────────
      page: "chat",
      setPage: (page) => set({ page }),

      // ── Config (persisted keys: openrouterKey, tavilyKey, model, temperature)
      config: { ...DEFAULT_CONFIG },
      setConfig: (partial) =>
        set((s) => ({ config: { ...s.config, ...partial } })),
      // Fetch server-side defaults (Brevo creds set as env vars on server).
      // Only fills fields the user hasn't already configured.
      fetchServerDefaults: async () => {
        try {
          const res = await fetch("/api/config/defaults");
          if (!res.ok) return;
          const defaults = await res.json();
          set((s) => ({
            config: {
              ...s.config,
              brevoApiKey:    s.config.brevoApiKey    || defaults.brevoApiKey    || "",
              brevoFromEmail: s.config.brevoFromEmail || defaults.brevoFromEmail || "",
            },
          }));
        } catch (_) { /* server not reachable — silent */ }
      },

      // ── Uploaded file ────────────────────────────────────────────────────────
      file: null,
      setFile: (file) => set({ file }),

      // ── Chat ─────────────────────────────────────────────────────────────────
      resetKey: 0,
      messages: [],
      chatStep: "welcome",
      addMessage: (msg) =>
        set((s) => ({ messages: [...s.messages, { id: Date.now() + Math.random(), ...msg }] })),
      updateLastBotMessage: (patch) =>
        set((s) => {
          const msgs = [...s.messages];
          for (let i = msgs.length - 1; i >= 0; i--) {
            if (msgs[i].role === "bot") { msgs[i] = { ...msgs[i], ...patch }; break; }
          }
          return { messages: msgs };
        }),
      setChatStep: (step) => set({ chatStep: step }),
      resetChat: () =>
        set((s) => ({
          messages: [], chatStep: "welcome",
          steps: [], progress: 0, result: null, analysisError: null,
          file: null, resetKey: s.resetKey + 1,
        })),

      // ── Analysis pipeline ────────────────────────────────────────────────────
      steps: [],
      progress: 0,
      result: null,
      analysisError: null,
      addStep: (step) =>
        set((s) => {
          const idx = s.steps.findIndex((x) => x.agent === step.agent);
          if (idx >= 0) {
            const u = [...s.steps]; u[idx] = { ...u[idx], ...step }; return { steps: u };
          }
          return { steps: [...s.steps, step] };
        }),
      updateStep: (agent, patch) =>
        set((s) => ({ steps: s.steps.map((x) => (x.agent === agent ? { ...x, ...patch } : x)) })),
      setProgress: (progress) => set({ progress }),
      setResult: (result) => set({ result }),
      setAnalysisError: (err) => set({ analysisError: err }),
    }),
    {
      name: "financeiq-config",
      // Only persist API credentials and model settings — never file, messages, results
      partialize: (s) => ({
        config: {
          openrouterKey:  s.config.openrouterKey,
          tavilyKey:      s.config.tavilyKey,
          model:          s.config.model,
          temperature:    s.config.temperature,
          brevoApiKey:    s.config.brevoApiKey,
          brevoFromEmail: s.config.brevoFromEmail,
        },
      }),
      // Deep-merge persisted config so non-persisted fields keep their defaults
      merge: (persisted, current) => {
        const cfg = { ...current.config, ...(persisted?.config ?? {}) };
        // Migrate every deprecated / removed model ID to a verified-working replacement
        const MODEL_MIGRATIONS = {
          // Mistral — all old IDs → GPT-4o Mini
          "mistralai/mistral-7b-instruct:free":          "openai/gpt-4o-mini",
          "mistralai/mistral-nemo:free":                 "openai/gpt-4o-mini",
          "mistralai/mistral-small-3.1-24b-instruct:free": "openai/gpt-4o-mini",
          // (Qwen old IDs migrated below)
          // DeepSeek free → paid (free versioned also gone)
          "deepseek/deepseek-r1:free":                   "openai/gpt-4o-mini",
          "deepseek/deepseek-chat:free":                 "openai/gpt-4o-mini",
          "deepseek/deepseek-chat-v3-0324:free":         "openai/gpt-4o-mini",
          // NVIDIA old IDs (non-current versions)
          "nvidia/llama-3.1-nemotron-70b-instruct:free": "nvidia/nemotron-3-super-120b-a12b:free",
          "nvidia/llama-3.3-nemotron-super-49b-v1:free": "nvidia/nemotron-3-super-120b-a12b:free",
          // Google / Microsoft deprecated
          "google/gemini-2.0-flash-exp:free":            "openai/gpt-4o-mini",
          "google/gemma-3-27b-it:free":                  "openai/gpt-4o-mini",
          "microsoft/phi-4:free":                        "openai/gpt-4o-mini",
          // Llama free — no response_format / JSON mode support
          "meta-llama/llama-3.3-70b-instruct:free":      "nvidia/nemotron-3-super-120b-a12b:free",
          "meta-llama/llama-3.1-8b-instruct:free":       "nvidia/nemotron-3-super-120b-a12b:free",
          // Broken Qwen old IDs → current Qwen free
          "qwen/qwen3-30b-a3b:free":                     "qwen/qwen3-next-80b-a3b-instruct:free",
          "qwen/qwen3-235b-a22b:free":                   "qwen/qwen3-next-80b-a3b-instruct:free",
          "qwen/qwen-2.5-72b-instruct:free":             "qwen/qwen3-next-80b-a3b-instruct:free",
          "qwen/qwen3.6-plus:free":                      "qwen/qwen3-next-80b-a3b-instruct:free",
        };
        if (cfg.model && MODEL_MIGRATIONS[cfg.model]) {
          cfg.model = MODEL_MIGRATIONS[cfg.model];
        }
        return { ...current, config: cfg };
      },
    }
  )
);

export const AGENT_ORDER = [
  "document_ingestion",
  "financial_analyzer",
  "debt_strategist",
  "savings_strategy",
  "budget_advisor",
  "report_generator",
];

export const MODELS = [
  // ── Paid — instant response, guaranteed uptime ────────────────────────────────
  { value: "openai/gpt-4o-mini",          label: "GPT-4o Mini",           tag: "Recommended" },
  { value: "openai/gpt-4o",               label: "GPT-4o",                tag: "Most Accurate" },
  { value: "openai/gpt-4-turbo",          label: "GPT-4 Turbo",           tag: "Powerful" },
  { value: "anthropic/claude-3.5-sonnet", label: "Claude 3.5 Sonnet",     tag: "Smart" },
  { value: "anthropic/claude-3.5-haiku",  label: "Claude 3.5 Haiku",      tag: "Fast · Cheap" },
  { value: "deepseek/deepseek-chat",      label: "DeepSeek V3",           tag: "Best Value" },
  { value: "google/gemini-flash-1.5",     label: "Gemini Flash 1.5",      tag: "Fast" },
  { value: "google/gemini-pro-1.5",       label: "Gemini Pro 1.5",        tag: "Balanced" },
  // ── Free — throttled to 10 s between agents (~60 s total runtime) ─────────────
  { value: "nvidia/nemotron-3-super-120b-a12b:free", label: "NVIDIA Nemotron 120B", tag: "Free · Best" },
  { value: "arcee-ai/trinity-mini:free",             label: "Arcee Trinity Mini",   tag: "Free · Fast" },
  { value: "minimax/minimax-m2.5:free",              label: "MiniMax M2.5",         tag: "Free · Data" },
  { value: "qwen/qwen3-next-80b-a3b-instruct:free",  label: "Qwen3 80B",           tag: "Free · Speed" },
];
