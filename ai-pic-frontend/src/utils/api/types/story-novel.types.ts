import type { Episode } from "./story.types";

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
  review_status: "ready" | "review_required";
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

export interface StoryNovelRevision {
  id: number;
  business_id: string;
  story_business_id?: string | null;
  task_id?: number | null;
  style: "zhihu" | "prose";
  target_words: number;
  chapter_count?: number | null;
  total_words?: number | null;
  revision_number: number;
  lifecycle_status: NovelLifecycle;
  continuity_status: ContinuityStatus;
  adaptation_plan_status: AdaptationPlanStatus;
  content_hash?: string | null;
  continuity_report?: { summary?: string; issues?: ContinuityIssue[] } | null;
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

export type AppliedNovelEpisodes = Episode[];
