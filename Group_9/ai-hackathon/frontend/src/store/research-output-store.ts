import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { ResearchSession } from "@/lib/types";

type OutputTab = "references" | "confidence" | "graph" | "trace";

type CachedSnapshot = {
  session: ResearchSession;
  cachedAt: string;
};

type GraphViewport = {
  x: number;
  y: number;
  zoom: number;
};

type PerSessionUiState = {
  activeTab: OutputTab;
  selectedSectionId: string | null;
  selectedSourceId: string | null;
  selectedNodeId: string | null;
  traceFilter: string;
  progressExpanded: boolean;
  expandedComparativeSections: string[];
  graphViewport: GraphViewport | null;
};

type ResearchOutputState = {
  currentSessionId: string | null;
  uiBySession: Record<string, PerSessionUiState>;
  cachedSessions: Record<string, CachedSnapshot>;
  setCurrentSession: (sessionId: string | null) => void;
  setActiveTab: (sessionId: string, tab: OutputTab) => void;
  setSelectedSection: (sessionId: string, sectionId: string | null) => void;
  setSelectedSource: (sessionId: string, sourceId: string | null) => void;
  setSelectedNode: (sessionId: string, nodeId: string | null) => void;
  setTraceFilter: (sessionId: string, filter: string) => void;
  setProgressExpanded: (sessionId: string, expanded: boolean) => void;
  toggleComparativeSection: (sessionId: string, section: string, expanded: boolean) => void;
  setGraphViewport: (sessionId: string, viewport: GraphViewport) => void;
  cacheSession: (session: ResearchSession) => void;
  getSessionUi: (sessionId: string) => PerSessionUiState;
};

const defaultUiState = (): PerSessionUiState => ({
  activeTab: "references",
  selectedSectionId: null,
  selectedSourceId: null,
  selectedNodeId: null,
  traceFilter: "",
  progressExpanded: false,
  expandedComparativeSections: [],
  graphViewport: null,
});

export const useResearchOutputStore = create<ResearchOutputState>()(
  persist(
    (set, get) => ({
      currentSessionId: null,
      uiBySession: {},
      cachedSessions: {},
      setCurrentSession: (sessionId) => set({ currentSessionId: sessionId }),
      setActiveTab: (sessionId, tab) =>
        set((state) => ({
          uiBySession: {
            ...state.uiBySession,
            [sessionId]: { ...ensureUiState(state.uiBySession[sessionId]), activeTab: tab },
          },
        })),
      setSelectedSection: (sessionId, sectionId) =>
        set((state) => ({
          uiBySession: {
            ...state.uiBySession,
            [sessionId]: { ...ensureUiState(state.uiBySession[sessionId]), selectedSectionId: sectionId },
          },
        })),
      setSelectedSource: (sessionId, sourceId) =>
        set((state) => ({
          uiBySession: {
            ...state.uiBySession,
            [sessionId]: { ...ensureUiState(state.uiBySession[sessionId]), selectedSourceId: sourceId },
          },
        })),
      setSelectedNode: (sessionId, nodeId) =>
        set((state) => ({
          uiBySession: {
            ...state.uiBySession,
            [sessionId]: { ...ensureUiState(state.uiBySession[sessionId]), selectedNodeId: nodeId },
          },
        })),
      setTraceFilter: (sessionId, filter) =>
        set((state) => ({
          uiBySession: {
            ...state.uiBySession,
            [sessionId]: { ...ensureUiState(state.uiBySession[sessionId]), traceFilter: filter },
          },
        })),
      setProgressExpanded: (sessionId, expanded) =>
        set((state) => ({
          uiBySession: {
            ...state.uiBySession,
            [sessionId]: { ...ensureUiState(state.uiBySession[sessionId]), progressExpanded: expanded },
          },
        })),
      toggleComparativeSection: (sessionId, section, expanded) =>
        set((state) => {
          const current = ensureUiState(state.uiBySession[sessionId]);
          const next = expanded
            ? Array.from(new Set([...current.expandedComparativeSections, section]))
            : current.expandedComparativeSections.filter((item) => item !== section);
          return {
            uiBySession: {
              ...state.uiBySession,
              [sessionId]: { ...current, expandedComparativeSections: next },
            },
          };
        }),
      setGraphViewport: (sessionId, viewport) =>
        set((state) => ({
          uiBySession: {
            ...state.uiBySession,
            [sessionId]: { ...ensureUiState(state.uiBySession[sessionId]), graphViewport: viewport },
          },
        })),
      cacheSession: (session) =>
        set((state) => ({
          currentSessionId: session.session_id,
          cachedSessions: {
            ...state.cachedSessions,
            [session.session_id]: {
              session,
              cachedAt: new Date().toISOString(),
            },
          },
          uiBySession: {
            ...state.uiBySession,
            [session.session_id]: ensureUiState(state.uiBySession[session.session_id]),
          },
        })),
      getSessionUi: (sessionId) => ensureUiState(get().uiBySession[sessionId]),
    }),
    {
      name: "ai-hackathon-research-output-store",
      partialize: (state) => ({
        currentSessionId: state.currentSessionId,
        uiBySession: state.uiBySession,
        cachedSessions: state.cachedSessions,
      }),
    },
  ),
);

function ensureUiState(state?: PerSessionUiState): PerSessionUiState {
  return {
    ...defaultUiState(),
    ...(state ?? {}),
  };
}
