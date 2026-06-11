export type TimelineResolvedVideoStatus = "ready" | "generating" | "missing";

export interface TimelineResolvedVideoItem {
  clip_id: string;
  status: TimelineResolvedVideoStatus;
  url?: string | null;
  source?: string | null;
  reason?: string | null;
  scene_id?: number | string | null;
  scene_number?: number | string | null;
  start_ms?: number | null;
  end_ms?: number | null;
  duration_seconds: number;
  task_id?: number | null;
  task_type?: string | null;
  task_status?: string | null;
  task_title?: string | null;
}

export interface TimelineResolvedVideoListResponse {
  timeline_id: number;
  timeline_version: number;
  ready: boolean;
  video_clip_count: number;
  missing_clip_count: number;
  generating_clip_count: number;
  items: TimelineResolvedVideoItem[];
}
