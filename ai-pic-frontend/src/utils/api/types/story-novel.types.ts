import type { Episode } from "./story.types";
import type { StoryNovelChapterLedger } from "./story-novel-continuity.types";
import type {
  NovelChapterLength,
  NovelChapterLengthOverrides,
  NovelGenerationLengthProfile,
  StoryNovelV4PlanFields,
  StoryNovelModelPolicy,
} from "./story-novel-planning.types";

export type NovelLifecycle = "legacy" | "draft" | "approved" | "superseded";
export type ContinuityStatus =
  | "unchecked"
  | "review_required"
  | "checking"
  | "passed"
  | "failed";
export type AdaptationPlanStatus =
  | "empty"
  | "draft"
  | "stale"
  | "approved"
  | "applied";

export interface StoryNovelChapter {
  business_id: string;
  position: number;
  title: string;
  content_text: string;
  summary?: string | null;
  cliffhanger?: string | null;
  review_status:
    | "ready"
    | "review_required"
    | "target_changed"
    | "length_mismatch";
  actual_chars?: number | null;
  generation_status?: string | null;
  extraction_status?: string | null;
  content_hash?: string | null;
  updated_at: string;
}

export interface ContinuityIssue {
  id: string;
  severity: "blocking" | "warning";
  chapter_business_ids?: string[];
  message: string;
  suggestion?: string;
  accepted_reason?: string;
}

export interface StoryNovelCanonItem {
  id: string;
  label?: string;
  name?: string;
  kind?: "character" | "location" | "object" | "organization" | "concept";
  [key: string]: unknown;
}

export interface StoryNovelCanon {
  timeline: StoryNovelCanonItem[];
  entities: StoryNovelCanonItem[];
  world_rules: StoryNovelCanonItem[];
  milestones: StoryNovelCanonItem[];
  character_arcs: Array<{
    character_id: string;
    start_state: string;
    checkpoints: Array<{ position: number; state: string }>;
    end_state: string;
  }>;
  initial_state: Record<string, Record<string, unknown>>;
  canon_hash?: string | null;
}

export interface StoryNovelChapterPlan {
  position: number;
  title: string;
  goal: string;
  key_events?: string[];
  character_focus?: string[];
  open_threads?: string[];
  end_state?: string;
  target_chars: number;
  min_chars?: number;
  max_chars?: number;
  length?: NovelChapterLength;
  actual_chars?: number;
  generation_status?: string;
  extraction_status?: string;
  preconditions?: Array<Record<string, unknown>>;
  required_event_ids?: string[];
  state_transitions?: Array<Record<string, unknown>>;
  knowledge_grants?: Array<Record<string, unknown>>;
  location_transitions?: Array<Record<string, unknown>>;
  milestones_consumed?: string[];
  forbidden_event_ids?: string[];
  payoffs_due?: string[];
  canon_refs?: string[];
  timeline_event_bindings?: Record<string, string>;
  entity_introductions?: Array<Record<string, unknown>>;
}

export interface AdaptationPlanEpisode {
  episode_number: number;
  title: string;
  source_chapter_business_ids: string[];
  adaptation_goal: string;
  summary: string;
  plot_points: string[];
  conflicts: string[];
  character_arcs: Record<string, unknown>;
  cliffhanger?: string | null;
}

export interface StoryNovelAdaptationPlan {
  version: number;
  novel_content_hash: string;
  episodes: AdaptationPlanEpisode[];
  applied_episode_ids?: number[];
}

export interface StoryNovelGenerationPlan extends StoryNovelV4PlanFields {
  schema?:
    | "story_novel_generation_plan.v2"
    | "story_novel_generation_plan.v3"
    | "story_novel_generation_plan.v4";
  version?: number;
  status: "planning" | "ready" | "failed";
  phase?: "spec_ready" | "canon" | "chapters" | "ready";
  canon?: StoryNovelCanon;
  canon_hash?: string;
  chapter_count?: number;
  target_chars?: number;
  planned_min_chars?: number;
  planned_target_chars?: number;
  planned_max_chars?: number;
  story_seed_version?: number;
  outline_hash?: string;
  plan_hash?: string;
  model_policy?: StoryNovelModelPolicy;
  planning_contract_version?: number;
  future_guard_hash?: string;
  length_profile?: NovelGenerationLengthProfile;
  chapter_length_overrides?: NovelChapterLengthOverrides;
  chapters: StoryNovelChapterPlan[];
}

export interface StoryNovelContinuityLedger {
  schema?:
    | "story_novel_continuity.v2"
    | "story_novel_continuity.v3"
    | "story_novel_continuity.v4"
    | "story_novel_continuity.v5";
  state_status?: "empty" | "generating" | "ready" | "stale" | "failed";
  stale_from_position?: number;
  recovery_from_position?: number;
  current_state?: Record<string, unknown>;
  chapters?: Record<string, StoryNovelChapterLedger>;
}

export interface StoryNovelQualityScore {
  score: number;
  rationale: string;
}

export interface StoryNovelRepairGroup {
  id: string;
  title?: string;
  issue_ids?: string[];
  canon_target?: {
    section:
      | "timeline"
      | "entities"
      | "world_rules"
      | "milestones"
      | "character_arcs"
      | "initial_state";
    item_id?: string;
    field?: string;
  };
  suggested_value?: unknown;
  affected_chapter_business_ids?: string[];
  earliest_position?: number;
}

export interface StoryNovelContinuityReport {
  schema?:
    | "story_novel_continuity_review.v2"
    | "story_novel_continuity_review.v3";
  summary?: string;
  issues?: ContinuityIssue[];
  hard_metrics?: Record<string, number>;
  quality_scores?: Record<string, StoryNovelQualityScore>;
  repair_groups?: StoryNovelRepairGroup[];
  report_hash?: string;
  canon_hash?: string;
  plan_version?: number;
  plan_hash?: string;
  status?: "stale";
  stale?: boolean;
}

export interface StoryNovelRevision {
  id: number;
  business_id: string;
  story_business_id?: string | null;
  task_id?: number | null;
  style: "zhihu" | "prose";
  target_words: number;
  model?: string | null;
  chapter_count?: number | null;
  total_words?: number | null;
  revision_number: number;
  lifecycle_status: NovelLifecycle;
  continuity_status: ContinuityStatus;
  adaptation_plan_status: AdaptationPlanStatus;
  content_hash?: string | null;
  generation_plan?: StoryNovelGenerationPlan | null;
  continuity_ledger?: StoryNovelContinuityLedger | null;
  continuity_report?: StoryNovelContinuityReport | null;
  adaptation_plan?: StoryNovelAdaptationPlan | null;
  approved_at?: string | null;
  created_at: string;
  updated_at?: string | null;
  chapters: StoryNovelChapter[];
}

export interface StoryNovelRevisionList {
  items: StoryNovelRevision[];
  canonical_business_id?: string | null;
}

export interface NovelTaskResponse {
  task_id: number;
  status: string;
  revision_business_id?: string | null;
}

export interface StoryNovelCanonUpdateResponse {
  revision: StoryNovelRevision;
  canon_hash: string;
  stale_from_position?: number | null;
}

export type AppliedNovelEpisodes = Episode[];
