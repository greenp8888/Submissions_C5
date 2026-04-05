export type RunMode = "single" | "batch";
export type Depth = "quick" | "standard" | "deep";
export type DatePreset = "last_30_days" | "last_90_days" | "last_1_year" | "last_5_years" | "all_time";
export type SourceChannel = "local_rag" | "web" | "arxiv";
export type ResearchStatus = "pending" | "running" | "complete" | "error";

export interface Source {
  id: string;
  url?: string | null;
  title: string;
  source_type: string;
  provider: string;
  author?: string | null;
  published_date?: string | null;
  credibility_score: number;
  relevance_score: number;
  rank: number;
  duplicate_of_source_id?: string | null;
  snippet: string;
  filename?: string | null;
  collection_id?: string | null;
  page_refs: number[];
  credibility_explanation: string;
  retrieval_reason: string;
  matched_time_window?: boolean | null;
  metadata: Record<string, unknown>;
}

export interface Finding {
  id: string;
  sub_question: string;
  content: string;
  snippet: string;
  quote_excerpt: string;
  filename?: string | null;
  page_refs: number[];
  source_ids: string[];
  agent: string;
}

export interface Claim {
  id: string;
  statement: string;
  supporting_source_ids: string[];
  contradicting_source_ids: string[];
  confidence: "low" | "medium" | "high";
  confidence_pct: number;
  reasoning: string;
  credibility_summary: string;
  evidence_summary: string;
  contested: boolean;
  weak_evidence: boolean;
  trust_score: number;
  debate_position: string;
  consensus_pct: number;
}

export interface Contradiction {
  id: string;
  claim_a_id: string;
  claim_a: string;
  source_a_id: string;
  source_a_label: string;
  claim_b_id: string;
  claim_b: string;
  source_b_id: string;
  source_b_label: string;
  analysis: string;
  resolution?: string | null;
  credibility_lean: string;
  weighting_rationale: string;
}

export interface Insight {
  id: string;
  content: string;
  evidence_chain: string[];
  insight_type: string;
  label: string;
}

export interface Entity {
  id: string;
  name: string;
  entity_type: string;
  description?: string | null;
  source_ids: string[];
}

export interface Relationship {
  source_entity_id: string;
  target_entity_id: string;
  relationship_type: string;
  description?: string | null;
}

export interface ReportSection {
  section_type: string;
  title: string;
  content: string;
  lead_summary: string;
  blocks: ReportBlock[];
  footer_notes: string[];
  visual?: ReportVisual | null;
  order: number;
}

export interface ReportCitation {
  source_id: string;
  label: string;
  title: string;
  url?: string | null;
}

export interface ReportMetaItem {
  label: string;
  value: string;
}

export interface ReportVisualPoint {
  label: string;
  value: number;
}

export interface ReportVisual {
  chart_type: string;
  title: string;
  description: string;
  unit: string;
  source_ids: string[];
  points: ReportVisualPoint[];
}

export interface ReportBlock {
  title: string;
  summary: string;
  narrative: string;
  citations: ReportCitation[];
  metadata: ReportMetaItem[];
  visual?: ReportVisual | null;
}

export interface FollowUpQuestion {
  question: string;
  rationale: string;
}

export interface ResearchEvent {
  event_type: string;
  timestamp: string;
  agent?: string | null;
  message: string;
  data: Record<string, unknown>;
}

export interface AgentTraceEntry {
  id: string;
  agent: string;
  step: string;
  input_summary?: string | null;
  output_summary?: string | null;
  timestamp: string;
  token_estimate?: number | null;
}

export interface KnowledgeDocument {
  id: string;
  collection_id: string;
  filename: string;
  document_type: string;
  checksum: string;
  upload_timestamp: string;
  status: string;
  page_count?: number | null;
  tags: string[];
  summary: string;
}

export interface LocalCollection {
  id: string;
  name: string;
  description?: string | null;
  created_at: string;
  document_ids: string[];
  shared_scope: string;
}

export interface ResearchSession {
  session_id: string;
  query: string;
  run_mode: RunMode;
  batch_topics: string[];
  enabled_sources: SourceChannel[];
  start_date?: string | null;
  end_date?: string | null;
  date_preset: DatePreset;
  depth: Depth;
  status: ResearchStatus;
  sub_questions: string[];
  sources: Source[];
  findings: Finding[];
  claims: Claim[];
  contradictions: Contradiction[];
  insights: Insight[];
  entities: Entity[];
  relationships: Relationship[];
  follow_up_questions: FollowUpQuestion[];
  report_sections: ReportSection[];
  events: ResearchEvent[];
  agent_trace: AgentTraceEntry[];
  uploaded_documents: KnowledgeDocument[];
  selected_collection_ids: string[];
  debate_mode: boolean;
  position_a?: string | null;
  position_b?: string | null;
  metadata: Record<string, unknown>;
}

export interface CollectionListResponse {
  collections: LocalCollection[];
}

export interface CollectionDetailsResponse {
  collection: LocalCollection;
  documents: KnowledgeDocument[];
}

export interface ProviderStatusEntry {
  status: string;
  configured: boolean;
  note?: string;
  model?: string;
}

export interface ProviderSettingsResponse {
  openrouter: ProviderStatusEntry;
  tavily: ProviderStatusEntry;
  arxiv: ProviderStatusEntry;
}

export interface ResearchFormValues {
  query: string;
  batchTopics: string;
  runMode: RunMode;
  debateEnabled: boolean;
  positionA: string;
  positionB: string;
  depth: Depth;
  enabledSources: SourceChannel[];
  startDate: string;
  endDate: string;
  datePreset: DatePreset;
  collectionIds: string[];
  files: File[];
}
