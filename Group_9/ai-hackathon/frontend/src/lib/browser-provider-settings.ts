const STORAGE_KEY = "ai-hackathon-provider-settings";

export interface BrowserProviderSettings {
  openrouter_api_key: string;
  tavily_api_key: string;
}

const EMPTY_SETTINGS: BrowserProviderSettings = {
  openrouter_api_key: "",
  tavily_api_key: "",
};

export function loadCachedProviderSettings(): BrowserProviderSettings {
  if (typeof window === "undefined") {
    return EMPTY_SETTINGS;
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return EMPTY_SETTINGS;
    }
    const parsed = JSON.parse(raw) as Partial<BrowserProviderSettings>;
    return {
      openrouter_api_key: typeof parsed.openrouter_api_key === "string" ? parsed.openrouter_api_key : "",
      tavily_api_key: typeof parsed.tavily_api_key === "string" ? parsed.tavily_api_key : "",
    };
  } catch {
    return EMPTY_SETTINGS;
  }
}

export function saveCachedProviderSettings(settings: BrowserProviderSettings) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}

export function clearCachedProviderSettings() {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(STORAGE_KEY);
}
