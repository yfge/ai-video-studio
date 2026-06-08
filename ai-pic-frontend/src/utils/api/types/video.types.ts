/**
 * Video and storyboard type definitions.
 */

// Storyboard video generation options
export interface StoryboardVideoGenerationOptions {
  model?: string;
  provider?: string;
  prompt?: string;
  duration?: number;
  fps?: number;
  resolution?: string;
  ratio?: string;
  watermark?: boolean;
  seed?: number;
  camera_fixed?: boolean;
  service_tier?: string;
  execution_expires_after?: number;
  return_last_frame?: boolean;
  camera_control?: Record<string, unknown>;
  use_end_frame?: boolean;
  mode?: string;
  cfg_scale?: number;
  motion_bucket_id?: number;
  method?: string;
  poll_interval_ms?: number;
  timeout_ms?: number;
}

// Video generation metadata
type StoryboardVideoGenerationMeta = {
  duration?: number;
  provider?: string;
  model?: string;
  method?: string;
  prompt?: string;
  resolution?: string;
  ratio?: string;
  start_image_url?: string;
  end_image_url?: string;
  thumbnail_url?: string;
  last_frame_url?: string;
} & Record<string, unknown>;

// Storyboard frame definition
export type StoryboardFrame = {
  frame_id?: string;
  frame_number?: number;
  scene_number?: number | string;
  scene_index?: number;
  shot_type?: string;
  camera_movement?: string;
  composition?: string;
  description?: string;
  duration_seconds?: number;
  start_ms?: number;
  end_ms?: number;
  ai_prompt?: string;
  reference_images?: string[];
  image_url?: string;
  start_image_url?: string;
  start_image_urls?: string[];
  end_image_url?: string;
  end_image_urls?: string[];
  video_url?: string;
  video_url_original?: string;
  video_urls?: string[];
  video_thumbnail_url?: string;
  video_thumbnail_url_original?: string;
  video_thumbnail_urls?: string[];
  video_last_frame_url?: string;
  video_last_frame_url_original?: string;
  video_last_frame_urls?: string[];
  video_generation?: StoryboardVideoGenerationMeta;
  generation_source?: string;
  generation_method?: string;
  generation_model?: string;
  status?: string;
  generated_at?: string;
  updated_at?: string;
  // Split frame linkage (from frame_duration_splitter)
  parent_frame_id?: string;
  split_index?: number;
  total_splits?: number;
  beat_range?: string;
  // Merged frame linkage
  merged_beat_ids?: string[];
} & Record<string, unknown>;

// Duration adjustment audit info (from frame_duration_splitter)
type DurationAdjustmentAudit = {
  frame_count?: number;
  splits_performed?: number;
  merges_performed?: number;
  audit_notes?: string[];
};

// Storyboard metadata
type StoryboardMeta = {
  version?: number;
  updated_at?: string;
  generation_source?: string;
  generation_method?: string;
  generation_model?: string;
  provider?: string;
  scene_scope?: number[] | null;
  duration_adjustment?: DurationAdjustmentAudit;
} & Record<string, unknown>;

// Storyboard plan frame
type StoryboardPlanFrame = {
  shot_type?: string;
  camera_movement?: string;
  composition?: string;
  intent?: string;
} & Record<string, unknown>;

// Storyboard plan scene
type StoryboardPlanScene = {
  scene_number: number;
  target_frames: number;
  frames: StoryboardPlanFrame[];
};

// Storyboard plan
type StoryboardPlan = {
  scenes: StoryboardPlanScene[];
} & Record<string, unknown>;

// Complete storyboard payload
export interface StoryboardPayload {
  frames: StoryboardFrame[];
  meta?: StoryboardMeta;
  plan?: StoryboardPlan;
}
