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
