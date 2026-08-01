import type { StorySeedStructuredChapter } from "./story-seed.types";

export interface NovelLengthRange {
  min_chars: number;
  target_chars: number;
  max_chars: number;
}

export interface NovelLengthProfile extends NovelLengthRange {
  profile_id: string;
  name: string;
  count_mode?: "non_whitespace_chars";
}

export interface NovelGenerationLengthProfile {
  profile_id: string;
  profile_name?: string;
  count_mode?: "non_whitespace_chars";
  default_min_chars: number;
  default_target_chars: number;
  default_max_chars: number;
}

export interface NovelChapterLength extends NovelLengthRange {
  source: "profile_default" | "chapter_override";
}

export type NovelChapterLengthOverrides = Record<string, NovelLengthRange>;

export interface StoryNovelPlanChapter extends StorySeedStructuredChapter {
  length?: NovelChapterLength;
  actual_chars?: number;
  generation_status?: string;
  extraction_status?: string;
}

export interface StoryNovelLengthSpecPayload {
  length_profile_id: string;
  custom_length_profile: NovelLengthRange | null;
  chapter_length_overrides: NovelChapterLengthOverrides;
}

export interface StoryNovelModelPolicy {
  planning_model: string | null;
  prose_model: string | null;
  audit_model: string | null;
}

export interface StoryNovelArcPlan {
  schema?: "story_novel_arc_plan.v1";
  arc_id: string;
  title: string;
  start_position: number;
  end_position: number;
  narrative_goal?: string;
  character_slots?: Array<Record<string, unknown>>;
  scope_slots?: Array<Record<string, unknown>>;
  instantiated_character_slots?: Array<Record<string, unknown>>;
  instantiated_scope_slots?: Array<Record<string, unknown>>;
  chapters?: Array<Record<string, unknown>>;
}

export interface StoryNovelV4PlanFields {
  series_bible?: Record<string, unknown>;
  series_bible_hash?: string;
  series_roadmap?: {
    schema?: string;
    arcs?: StoryNovelArcPlan[];
    chapters?: Array<{ position: number; arc_id: string }>;
  };
  series_roadmap_hash?: string;
  current_arc_plan?: StoryNovelArcPlan;
  current_arc_plan_hash?: string;
  arc_plans?: Record<string, StoryNovelArcPlan>;
  arc_plans_hash?: string;
  frozen_through_position?: number;
  scope_graph?: {
    taxonomy?: Array<Record<string, unknown>>;
    nodes?: Array<Record<string, unknown>>;
    edges?: Array<Record<string, unknown>>;
  };
  scope_graph_hash?: string;
  planner_snapshot_schema?: string;
  chapter_intent_schema?: string;
  chapter_contract_schema?: string;
  audit_proof_schema?: string;
}

export interface StoryNovelCreateRevisionPayload
  extends StoryNovelLengthSpecPayload {
  style: "prose";
  model?: string;
  model_policy: StoryNovelModelPolicy;
}

export interface StoryNovelUpdateLengthSpecPayload
  extends StoryNovelLengthSpecPayload {
  expected_plan_version: number;
  model?: string | null;
  model_policy: StoryNovelModelPolicy;
}
