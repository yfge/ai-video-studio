/**
 * Script type definitions.
 */
import type { AdSnippet, HookPlan } from "./story.types";

// Script entity
export interface Script {
  id: number;
  business_id: string;
  episode_id: number;
  episode_business_id?: string | null;
  title: string;
  content?: string;
  scenes?: unknown[];
  dialogues?: unknown[];
  stage_directions?: unknown[];
  format_type: string;
  language: string;
  page_count?: number;
  word_count?: number;
  character_count?: number;
  status: string;
  version: string;
  tags?: string[];
  extra_metadata?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  generation_prompt?: string;
  ai_model?: string;
  generation_params?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// Script generation request
export interface ScriptGenerationRequest {
  episode_id: number;
  generation_mode?: "standard" | "production";
  auto_timeline_pipeline?: boolean | null;
  format_type: string;
  language: string;
  template_style?: "commercial_vertical_drama" | "structured_json";
  target_chars_per_episode?: number;
  quality_threshold?: number;
  dialogue_style: string;
  scene_detail_level: string;
  market_region?: string;
  micro_genre?: string;
  hook_plan?: HookPlan;
  twist_density?: string;
  cliffhanger_plan?: string[];
  ad_snippets?: AdSnippet[];
  pacing_template?: string;
  page_count?: number;
  scene_count?: number;
  dialogue_ratio?: number;
  action_ratio?: number;
  style_notes?: string;
  additional_requirements?: string;
  style_preferences?: string[];
  model?: string;
  temperature?: number;
}

// Normalized scene structure
export interface NormalizedScene {
  id: number;
  scene_number: string;
  slug_line: string;
  status: string;
  environment_id?: number | null;
  environment_type?: string | null;
  location?: string | null;
  time_of_day?: string | null;
  summary?: string | null;
  metadata?: Record<string, unknown>;
}

// Scene beat (dialogue/action unit)
export interface SceneBeat {
  id: number;
  business_id?: string;
  scene_id: number;
  scene_business_id?: string | null;
  order_index: number;
  beat_type?: string | null;
  beat_summary?: string | null;
  characters_involved?: Record<string, unknown> | null;
  dialogue_excerpt?: string | null;
  camera_notes?: string | null;
  duration_seconds?: number | null;
  metadata?: Record<string, unknown> | null;
  created_at?: string;
  updated_at?: string;
}

// Normalized shot structure
export interface NormalizedShot {
  id: number;
  shot_number: string;
  shot_type?: string;
  camera_movement?: string;
  scene_beat_id?: number | null;
  character_ids?: number[] | null;
}
