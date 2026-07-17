export type ProductionCanvasAssetPolicy =
  | "reuse_preferred"
  | "reuse_only"
  | "create_if_missing"
  | "create_new"
  | "ask_if_ambiguous";

export interface ProductionCanvasClarificationOption {
  label: string;
  value: string;
}

export interface ProductionCanvasClarification {
  id: string;
  field: string;
  question: string;
  reason: string;
  required: boolean;
  options: ProductionCanvasClarificationOption[];
  answer?: string | null;
}

export interface ProductionCanvasBriefOverrides {
  title?: string;
  duration_seconds?: number;
  episode_count?: number;
  aspect_ratio?: "9:16" | "16:9" | "1:1";
  resolution?: string;
  fps?: number;
  text_model?: string;
  image_model?: string;
  video_model?: string;
  visual_style?: string;
}

export interface ProductionCanvasVideoSpec {
  duration_seconds?: number | null;
  episode_count?: number | null;
  focus_episode_number?: number | null;
  aspect_ratio?: "9:16" | "16:9" | "1:1" | null;
  resolution?: string | null;
  fps?: number | null;
  visual_style: string[];
}

export interface ProductionCanvasModelChoice {
  requested?: string | null;
  selected?: string | null;
  provider?: string | null;
  status: "requested" | "auto_selected" | "pipeline_default" | "unavailable";
  reason: string;
}

export interface ProductionCanvasProductionBrief {
  version: string;
  source_prompt: string;
  interpretation_status:
    | "model_parsed"
    | "deterministic_compatibility"
    | "failed";
  interpretation_warnings: string[];
  intent: {
    kind: string;
    objective: string;
    narrative_seed: string;
    genre?: string | null;
    tone: string[];
    target_audience?: string | null;
    language: string;
    must_include: string[];
    must_avoid: string[];
  };
  video_spec: ProductionCanvasVideoSpec;
  models: {
    text: ProductionCanvasModelChoice;
    image: ProductionCanvasModelChoice;
    video: ProductionCanvasModelChoice;
  };
  assets: {
    virtual_ip_name?: string | null;
    virtual_ip_description?: string | null;
    environment_names: string[];
    asset_policy: ProductionCanvasAssetPolicy;
  };
  conflicts: Array<Record<string, string | null>>;
  clarifications: ProductionCanvasClarification[];
  ready_for_execution: boolean;
}

export interface ProductionCanvasContentPlan {
  version: string;
  title: string;
  premise: string;
  synopsis: string;
  main_conflict: string;
  theme?: string | null;
  characters: Array<{
    name: string;
    role: string;
    description: string;
    season_arc?: string | null;
    continuity_anchors: string[];
  }>;
  environments: Array<{
    name: string;
    purpose: string;
    reuse_across_episodes: boolean;
  }>;
  season_arc: string;
  recurring_engine: string;
  episodes: Array<{
    episode_number: number;
    title: string;
    logline: string;
    beats: string[];
    payoff: string;
    cliffhanger: string;
    continuity_handoff: string[];
  }>;
  continuity_rules: string[];
  future_threads: string[];
}

export interface ProductionCanvasProductionContext {
  version: string;
  brief: ProductionCanvasProductionBrief;
  content_plan: ProductionCanvasContentPlan;
  asset_associations: Array<{
    kind: "virtual_ip" | "environment";
    requested_name?: string | null;
    decision: "reused" | "created" | "ambiguous" | "missing" | "not_required";
    asset_id?: number | null;
    asset_name?: string | null;
    candidate_ids: number[];
    reason: string;
  }>;
  selected_asset_ids: Record<string, number[]>;
  created_story_ids: number[];
  created_episode_ids: number[];
}
