export type StoryNovelGenerationStage =
  | "arc_planning"
  | "chapter_planning"
  | "prose"
  | "audit"
  | "local_repair"
  | "memory_ready"
  | "ready";

export interface StoryNovelStageMetric {
  calls: number;
  input_tokens?: number;
  output_tokens?: number;
  latency_ms?: number;
}

export interface StoryNovelChapterLedger {
  status?:
    | "chapter_planning"
    | "body_ready"
    | "audit"
    | "memory_ready"
    | "ready"
    | "stale"
    | "snapshot_stale"
    | "state_pending"
    | "gate_failed";
  stage?: StoryNovelGenerationStage;
  stage_metrics?: Partial<
    Record<StoryNovelGenerationStage, StoryNovelStageMetric>
  >;
  failed_block_ids?: string[];
  generation_status?: string;
  extraction_status?: "pending" | "ready" | "stale" | "blocked";
  char_count?: number;
  body_hash?: string;
  source_hash?: string;
  canon_hash?: string;
  context_hash?: string;
  state_before_hash?: string;
  state_after_hash?: string;
  state_validation?: {
    status?: "passed" | "failed";
    violations?: Array<{ code: string; message: string }>;
  };
  body_repair_count?: number;
  state_extraction_repair_count?: number;
  planner_snapshot_hash?: string;
  arc_planner_snapshot_hash?: string;
  chapter_intent_hash?: string;
  chapter_intent?: {
    entity_proposals?: Array<{
      proposal_handle?: string;
      kind?: string;
      name?: string;
      transient?: boolean;
    }>;
  };
  model_call_snapshots?: Record<
    string,
    { snapshot_hash?: string; input_hash?: string }
  >;
}
