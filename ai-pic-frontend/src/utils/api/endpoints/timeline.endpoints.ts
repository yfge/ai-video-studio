/**
 * Timeline Spec v1 API endpoints.
 */

import { httpClient } from "../client";
import type { ApiResponse } from "../types/common.types";
import type {
  TimelineClipAssetListParams,
  TimelineClipAssetListResponse,
  TimelineListResponse,
  TimelineRenderJobCreate,
  TimelineRenderJobListResponse,
  TimelineRenderJobResponse,
  TimelineResponse,
} from "../types/timeline.types";

export async function listEpisodeTimelines(
  episodeId: number | string,
): Promise<ApiResponse<TimelineListResponse>> {
  return httpClient<TimelineListResponse>(
    `/api/v1/episodes/${episodeId}/timelines`,
  );
}

export async function getTimeline(
  timelineId: number | string,
): Promise<ApiResponse<TimelineResponse>> {
  return httpClient<TimelineResponse>(`/api/v1/timelines/${timelineId}`);
}

export async function queueTimelineRender(
  timelineId: number | string,
  payload: TimelineRenderJobCreate,
): Promise<ApiResponse<TimelineRenderJobResponse>> {
  return httpClient<TimelineRenderJobResponse>(
    `/api/v1/timelines/${timelineId}/render`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function listTimelineRenderJobs(
  timelineId: number | string,
): Promise<ApiResponse<TimelineRenderJobListResponse>> {
  return httpClient<TimelineRenderJobListResponse>(
    `/api/v1/timelines/${timelineId}/render-jobs`,
  );
}

export async function listTimelineClipAssets(
  timelineId: number | string,
  params: TimelineClipAssetListParams = {},
): Promise<ApiResponse<TimelineClipAssetListResponse>> {
  const query = new URLSearchParams();
  if (params.timelineVersion != null) {
    query.set("timeline_version", String(params.timelineVersion));
  }
  if (params.clipId) {
    query.set("clip_id", params.clipId);
  }
  if (params.includeDeleted) {
    query.set("include_deleted", "true");
  }
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return httpClient<TimelineClipAssetListResponse>(
    `/api/v1/timelines/${timelineId}/clip-assets${suffix}`,
  );
}

export const timelineAPI = {
  listEpisodeTimelines,
  getTimeline,
  queueTimelineRender,
  listTimelineRenderJobs,
  listTimelineClipAssets,
};
