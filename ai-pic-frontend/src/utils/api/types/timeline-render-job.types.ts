import type { TimelineMediaAssetResponse } from "./timeline.types";

export type TimelineRenderType = "proxy" | "final" | "export";
type TimelineRenderStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled";

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
