export interface ContinuityIssue {
  id: string;
  severity: "blocking" | "warning";
  chapter_business_ids?: string[];
  message: string;
  suggestion?: string;
  accepted_reason?: string;
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
    | "story_novel_continuity_review.v3"
    | "story_novel_continuity_review.v4";
  summary?: string;
  issues?: ContinuityIssue[];
  hard_metrics?: Record<string, number>;
  quality_scores?: Record<string, StoryNovelQualityScore>;
  repair_groups?: StoryNovelRepairGroup[];
  report_hash?: string;
  canon_hash?: string;
  plan_version?: number;
  plan_hash?: string;
  status?: "passed" | "failed" | "stale";
  stale?: boolean;
}
