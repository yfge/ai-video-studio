import type { ProductionCanvasResolvedContext } from "./production-canvas-context.types";

interface HookBeat {
  beat_type?: string;
  description: string;
  timing?: string;
  intensity?: string;
}

export interface HookPlan {
  opening_hook?: string;
  escalation_plan?: string;
  payoff_plan?: string;
  key_reversals?: HookBeat[];
}

export interface AdSnippet {
  duration_seconds?: number;
  hook: string;
  visual_summary?: string;
  call_to_action?: string;
}

export interface StoryCharacter {
  id: number;
  business_id: string;
  story_id: number;
  importance: number;
  virtual_ip_id: number;
  virtual_ip_business_id?: string | null;
  virtual_ip_name?: string | null;
  name?: string | null;
  display_name?: string | null;
  character_name?: string | null;
  role_type?: string;
  role?: string | null;
  description?: string | null;
  appearance?: string | null;
  personality?: string;
  background?: string;
  motivation?: string;
  character_arc?: string;
  backstory?: string | null;
  relationships?: Record<string, unknown>;
  arc_summary?: string | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

// Story entity
export interface Story {
  id: number;
  business_id: string;
  title: string;
  genre: string;
  theme?: string;
  target_audience?: string;
  duration_minutes?: number;
  default_aspect_ratio?: "9:16" | "16:9";
  workflow_mode?: "direct" | "novel_adaptation_v1";
  canonical_novel_export_id?: number | null;
  premise?: string;
  synopsis?: string;
  main_conflict?: string;
  resolution?: string;
  main_characters?: unknown[];
  character_relationships?: Record<string, unknown>;
  setting_time?: string;
  setting_location?: string;
  world_building?: string;
  character_ids?: number[];
  characters?: StoryCharacter[];
  plot_points?: unknown[];
  status: string;
  is_public: boolean;
  tags?: string[];
  extra_metadata?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  generation_prompt?: string;
  ai_model?: string;
  generation_params?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  story_characters?: StoryCharacter[];
}

// Episode entity
export interface Episode {
  id: number;
  business_id: string;
  story_id: number;
  story_business_id?: string | null;
  episode_number: number;
  title: string;
  aspect_ratio?: "9:16" | "16:9" | null;
  summary?: string;
  synopsis?: string;
  plot_points?: unknown[];
  character_arcs?: Record<string, unknown>;
  conflicts?: unknown[];
  duration_minutes?: number;
  scene_count?: number;
  key_events?: string[];
  focus_characters?: number[];
  theme?: string;
  runtime_minutes?: number;
  status: string;
  tags?: string[];
  extra_metadata?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  generation_prompt?: string;
  ai_model?: string;
  generation_params?: Record<string, unknown>;
  source_novel_export_id?: number | null;
  source_novel_export_business_id?: string | null;
  source_chapter_refs?: Array<Record<string, unknown>> | null;
  created_at: string;
  updated_at: string;
}

// Story generation request
export interface StoryGenerationRequest {
  title: string;
  genre: string;
  workflow_mode?: "direct" | "novel_adaptation_v1";
  market_region?: string;
  micro_genre?: string;
  hook_plan?: HookPlan;
  twist_density?: string;
  cliffhanger_plan?: string[];
  ad_snippets?: AdSnippet[];
  pacing_template?: string;
  theme?: string;
  target_audience?: string;
  duration_minutes?: number;
  default_aspect_ratio?: "9:16" | "16:9";
  character_ids: number[];
  setting_time?: string;
  setting_location?: string;
  world_building?: string;
  additional_requirements?: string;
  style_preferences?: string[];
  content_restrictions?: string[];
  tags?: string[];
  model?: string;
  temperature?: number;
}

// Episode generation request
export interface EpisodeGenerationRequest {
  story_id: number;
  episode_count: number;
  episode_duration?: number;
  market_region?: string;
  micro_genre?: string;
  hook_plan?: HookPlan;
  twist_density?: string;
  cliffhanger_plan?: string[];
  ad_snippets?: AdSnippet[];
  pacing_template?: string;
  focus_characters?: number[];
  plot_complexity: string;
  pacing: string;
  additional_requirements?: string;
  style_preferences?: string[];
  model?: string;
  temperature?: number;
}

export interface SingleVideoProjectRequest {
  title: string;
  prompt: string;
  duration_minutes?: number;
  duration_seconds?: number;
  aspect_ratio?: "9:16" | "16:9" | "1:1";
  style?: string;
  virtual_ip_id?: number;
  environment_id?: number;
  start_generation?: boolean;
}

export interface SingleVideoProjectResponse {
  story_id: number;
  story_business_id: string;
  episode_id: number;
  episode_business_id: string;
  task_id?: number | null;
  task_status?: string | null;
  context: ProductionCanvasResolvedContext;
}

// Readiness check types
type ReadinessSeverity = "CRITICAL" | "ERROR" | "WARNING" | "INFO";

export interface ReadinessCheck {
  name: string;
  passed: boolean;
  severity: ReadinessSeverity;
  message: string;
  suggestion?: string | null;
}

export interface ReadinessResult {
  ready: boolean;
  can_proceed: boolean;
  story_id: number;
  episode_id?: number | null;
  checks: ReadinessCheck[];
  summary: string;
  critical_issues: ReadinessCheck[];
  errors: ReadinessCheck[];
  warnings: ReadinessCheck[];
  info_issues: ReadinessCheck[];
  failed_count: number;
  passed_count: number;
}

// Quick-fix types
interface FixApplied {
  check_name: string;
  field: string;
  old_value: string | null;
  new_value: string;
}

interface FixSkipped {
  check_name: string;
  reason: string;
}

interface QuickFixImprovement {
  initial_failed: number;
  final_failed: number;
  fixed_count: number;
}

export interface QuickFixRequest {
  dry_run?: boolean;
}

export interface QuickFixResponse {
  story_id: number;
  dry_run: boolean;
  fixes_applied: FixApplied[];
  fixes_skipped: FixSkipped[];
  initial_readiness: ReadinessResult;
  final_readiness: ReadinessResult;
  improvement: QuickFixImprovement;
}
