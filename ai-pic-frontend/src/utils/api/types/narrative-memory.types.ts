export type NarrativeCandidateStatus =
  | "candidate"
  | "approved"
  | "rejected"
  | "stale"
  | "superseded";

export interface MemorySummary {
  canon_branch_id: string;
  private_memory_count: number;
  shared_baseline_version: number;
  shared_baseline_hash?: string | null;
  latest_snapshot_hash?: string | null;
  pending_count: number;
  conflict_count: number;
  stale_count: number;
  memory_review_status: string;
}

export interface SharedMemoryBaselineDiff {
  frozen_version: number;
  available_version: number;
  frozen_hash?: string | null;
  available_hash?: string | null;
  added: Array<Record<string, unknown>>;
  removed: Array<Record<string, unknown>>;
  modified: Array<{
    before: Record<string, unknown>;
    after: Record<string, unknown>;
  }>;
  has_updates: boolean;
}

export interface NarrativeAnchor {
  business_id: string;
  story_business_id: string;
  canon_branch_id: string;
  anchor_type: "chapter" | "episode" | "scene" | "beat" | "between";
  narrative_sequence: number;
  story_time_order?: number | null;
  story_time_label?: string | null;
  source_artifact_type: string;
  source_artifact_business_id: string;
  source_version: number;
  source_hash: string;
  after_anchor_business_id?: string | null;
  before_anchor_business_id?: string | null;
  status: string;
  version: number;
}

export interface NarrativeEvent {
  business_id: string;
  story_business_id: string;
  event_type: string;
  summary: string;
  participant_character_ids: string[];
  occurred_at_anchor_business_id: string;
  presentation: "on_screen" | "offscreen" | "withheld";
  audience_disclosure: "hidden" | "hinted" | "partial" | "revealed";
  status: NarrativeCandidateStatus;
  source_artifact_business_id: string;
  source_hash: string;
  candidate_evidence?: Record<string, unknown> | null;
  invalidation?: Record<string, unknown> | null;
  version: number;
}

export interface CharacterMemory {
  business_id: string;
  story_business_id?: string | null;
  canon_branch_id?: string;
  character_business_id?: string | null;
  virtual_ip_business_id: string;
  scope: "story_private" | "character_shared";
  memory_type: string;
  content: string;
  belief?: string | null;
  belief_confidence?: number | null;
  emotional_impact: string[];
  salience: number;
  occurred_at_anchor_business_id?: string | null;
  learned_at_anchor_business_id: string;
  effective_from_anchor_business_id: string;
  invalidated_at_anchor_business_id?: string | null;
  status: NarrativeCandidateStatus;
  source_hash: string;
  supersedes_business_id?: string | null;
  invalidation?: Record<string, unknown> | null;
  version: number;
}

export interface MemoryPromotion {
  business_id: string;
  source_story_business_id: string;
  source_memory_ids: string[];
  target_virtual_ip_business_id: string;
  candidate_content: string;
  status: string;
  decision_reason?: string | null;
  result_shared_memory_business_id?: string | null;
  version: number;
  approved_by?: number | null;
  approved_at?: string | null;
  created_at: string;
  updated_at: string;
}

export type ExpressionPolicy = "sayable" | "subtext_only" | "must_not_reveal";

export interface DramaticState {
  schema: "dramatic_state.v1";
  valid_from_anchor_id?: string | null;
  valid_until_anchor_id?: string | null;
  scene_objective?: string | null;
  character_intents: Array<{
    character_business_id: string;
    surface_action: string;
    hidden_goal?: string | null;
    emotional_truth?: string | null;
    expression_policy: ExpressionPolicy;
  }>;
  audience_goal?: string | null;
  audience_disclosure: "hidden" | "hinted" | "partial" | "revealed";
  must_hint: string[];
  must_not_reveal: string[];
}

export interface DramaticStateResponse {
  scene_business_id: string;
  version: number;
  state_hash: string;
  dramatic_state: DramaticState;
  quality_gate: {
    passed: boolean;
    blocking_issues: Array<Record<string, unknown>>;
  };
  suggestion?: DramaticState | null;
  suggestion_based_on_version?: number | null;
  available_memory_preview: Array<{
    character_business_id?: string | null;
    snapshot_hash?: string | null;
    memories: Array<Record<string, unknown>>;
    growth_state: Record<string, unknown>;
  }>;
}
