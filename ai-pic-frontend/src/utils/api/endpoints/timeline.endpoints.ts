/**
 * Timeline Spec v1 API endpoints.
 */

import { httpClient } from "../client";
import type { ApiResponse } from "../types/common.types";
import type {
  TimelineClipAssetListParams,
  TimelineClipAssetListResponse,
  TimelineClipAssetResponse,
  TimelineClipReworkRequest,
  TimelineClipVideoReworkTaskRequest,
  TimelineClipVideoReworkTaskResponse,
  TimelineListResponse,
  TimelineRenderJobCreate,
  TimelineRenderJobListResponse,
  TimelineRenderJobResponse,
  TimelineResponse,
  TimelineStoryboardGridGenerateRequest,
  TimelineStoryboardGridGenerateResponse,
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

export async function reworkTimelineClip(
  timelineId: number | string,
  clipId: string,
  payload: TimelineClipReworkRequest,
): Promise<ApiResponse<TimelineClipAssetResponse>> {
  return httpClient<TimelineClipAssetResponse>(
    `/api/v1/timelines/${timelineId}/clips/${encodeURIComponent(
      clipId,
    )}/rework`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function queueTimelineClipVideoRework(
  timelineId: number | string,
  clipId: string,
  payload: TimelineClipVideoReworkTaskRequest,
): Promise<ApiResponse<TimelineClipVideoReworkTaskResponse>> {
  return httpClient<TimelineClipVideoReworkTaskResponse>(
    `/api/v1/timelines/${timelineId}/clips/${encodeURIComponent(
      clipId,
    )}/rework/video`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function generateTimelineStoryboardGrid(
  timelineId: number | string,
  payload: TimelineStoryboardGridGenerateRequest,
): Promise<ApiResponse<TimelineStoryboardGridGenerateResponse>> {
  return httpClient<TimelineStoryboardGridGenerateResponse>(
    `/api/v1/timelines/${timelineId}/storyboard-grid/generate`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export const timelineAPI = {
  listEpisodeTimelines,
  getTimeline,
  queueTimelineRender,
  listTimelineRenderJobs,
  listTimelineClipAssets,
  reworkTimelineClip,
  queueTimelineClipVideoRework,
  generateTimelineStoryboardGrid,
};
