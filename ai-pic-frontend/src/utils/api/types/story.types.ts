/**
 * Story and episode type definitions.
 */

// Hook/traffic planning types
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

// Story character reference
export interface StoryCharacter {
  id: number;
  business_id: string;
  story_id: number;
  importance: number;
  virtual_ip_id: number;
  virtual_ip_business_id?: string | null;
  name?: string;
  character_name?: string;
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
  created_at: string;
  updated_at: string;
}

// Story generation request
export interface StoryGenerationRequest {
  title: string;
  genre: string;
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
