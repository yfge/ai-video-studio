/**
 * Timeline Spec v1 API type definitions.
 */

export interface TimelineClip {
  clip_id: string;
  track_type: string;
  scene_id?: number | string | null;
  scene_number?: number | string | null;
  beat_id?: number | string | null;
  beat_type?: string | null;
  ordinal?: number | null;
  start_ms: number;
  end_ms: number;
  duration_ms?: number | null;
  timing_source?: string | null;
  source_refs?: Record<string, unknown>;
  text?: string | null;
  speaker_name?: string | null;
  asset_ref?: Record<string, unknown> | null;
  [key: string]: unknown;
}

export interface TimelineTrackSpec {
  track_type: string;
  clips: TimelineClip[];
  [key: string]: unknown;
}

export interface TimelineSpec {
  spec_version: string;
  episode_id: number;
  episode_business_id?: string | null;
  script_id: number;
  script_business_id?: string | null;
  version: number;
  source_audio_timeline_version?: number | null;
  duration_ms?: number | null;
  source?: Record<string, unknown>;
  tracks: TimelineTrackSpec[];
  support_views?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface TimelineResponse {
  id: number;
  business_id: string;
  episode_id: number;
  episode_business_id?: string | null;
  script_id: number;
  script_business_id?: string | null;
  title: string;
  status: string;
  spec: TimelineSpec;
  version: number;
  source_audio_timeline_version?: number | null;
  created_by?: number | null;
  updated_by?: number | null;
  created_at: string;
  updated_at: string;
}

export interface TimelineListResponse {
  items: TimelineResponse[];
}

export interface TimelineUpdateRequest {
  expected_version: number;
  title?: string | null;
  status?: string | null;
  spec?: TimelineSpec | null;
  source_audio_timeline_version?: number | null;
}

export type TimelineRenderType = "proxy" | "final" | "export";
type TimelineRenderStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled";

interface TimelineMediaAssetResponse {
  id: number;
  business_id: string;
  asset_type: string;
  origin: string;
  file_url?: string | null;
  object_key?: string | null;
  file_path?: string | null;
  mime_type?: string | null;
  hash?: string | null;
  duration_ms?: number | null;
  width?: number | null;
  height?: number | null;
  metadata?: Record<string, unknown> | null;
  created_by?: number | null;
  created_at: string;
  updated_at: string;
}

export interface TimelineClipAssetResponse {
  id: number;
  business_id: string;
  timeline_id: number;
  timeline_version: number;
  clip_id: string;
  track_type?: string | null;
  asset_role: string;
  media_asset_id: number;
  media_asset?: TimelineMediaAssetResponse | null;
  render_job_id?: number | null;
  source?: string | null;
  source_ref?: Record<string, unknown> | null;
  replacement_of_id?: number | null;
  is_deleted?: boolean;
  deleted_at?: string | null;
  deleted_by?: number | null;
  deleted_reason?: string | null;
  created_by?: number | null;
  created_at: string;
}

export interface TimelineClipAssetListResponse {
  items: TimelineClipAssetResponse[];
}

export interface TimelineClipAssetListParams {
  timelineVersion?: number | null;
  clipId?: string | null;
  includeDeleted?: boolean;
}

export type TimelineClipReworkAction = "re_dub" | "re_cut" | "re_render";
export type TimelineClipVideoReworkAction = "re_cut" | "re_render";
export type TimelineClipVideoReferenceMode =
  | "start_end"
  | "clip_storyboard_panel"
  | "storyboard_grid_panel";
type TimelineStoryboardGridStyle = "2d_cartoon" | "3d_cartoon" | "live_action";
export type TimelineClipStoryboardStyle = TimelineStoryboardGridStyle;

export interface TimelineClipReworkRequest {
  expected_version: number;
  action: TimelineClipReworkAction;
  media_asset_id: number;
  asset_role?: string | null;
  reason?: string | null;
}

export interface TimelineClipVideoReworkTaskRequest {
  expected_version: number;
  action: TimelineClipVideoReworkAction;
  prompt?: string | null;
  model?: string | null;
  duration?: number | null;
  fps?: number;
  resolution?: string;
  ratio?: string | null;
  asset_role?: string | null;
  reason?: string | null;
  use_end_frame?: boolean;
  return_last_frame?: boolean;
  reference_mode?: TimelineClipVideoReferenceMode | null;
  use_clip_storyboard?: boolean;
  use_storyboard_grid?: boolean;
  reference_images?: string[] | null;
}

export interface TimelineClipVideoReworkTaskResponse {
  task_id: number;
  status: string;
}

export interface TimelineClipStoryboardGenerateRequest {
  expected_version: number;
  panel_count?: number;
  style?: TimelineClipStoryboardStyle;
  model?: string | null;
  generation_profile?: string | null;
  size?: string | null;
  aspect_ratio?: string | null;
  width?: number | null;
  height?: number | null;
  reference_images?: string[] | null;
  character_virtual_ip_ids?: number[] | null;
}

export interface TimelineClipStoryboardGenerateResponse {
  task_id: number;
  status: string;
}

export interface TimelineRenderJobCreate {
  timeline_version: number;
  render_type: TimelineRenderType;
  preset?: Record<string, unknown>;
  force_new_attempt?: boolean;
}

export interface TimelineRenderJobResponse {
  id: number;
  business_id: string;
  timeline_id: number;
  timeline_version: number;
  render_type: TimelineRenderType | string;
  preset_hash: string;
  preset: Record<string, unknown>;
  status: TimelineRenderStatus | string;
  progress: number;
  output_asset_id?: number | null;
  output_asset?: TimelineMediaAssetResponse | null;
  log?: Record<string, unknown> | null;
  created_by?: number | null;
  created_at: string;
  updated_at: string;
}

export interface TimelineRenderJobListResponse {
  items: TimelineRenderJobResponse[];
}
