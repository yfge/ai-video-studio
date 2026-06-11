/**
 * Timeline Spec v1 API endpoints.
 */

import { httpClient } from "../client";
import type { ApiResponse } from "../types/common.types";
import type {
  TimelineClipAssetListParams,
  TimelineClipAssetListResponse,
  TimelineClipAssetResponse,
  TimelineClipKeyframeGenerateRequest,
  TimelineClipKeyframeGenerateResponse,
  TimelineClipReworkRequest,
  TimelineResolvedVideoListResponse,
  TimelineClipStoryboardGenerateRequest,
  TimelineClipStoryboardGenerateResponse,
  TimelineClipTaskListResponse,
  TimelineClipVideoReworkTaskRequest,
  TimelineClipVideoReworkTaskResponse,
  TimelineListResponse,
  TimelineRenderJobCreate,
  TimelineRenderJobListResponse,
  TimelineRenderJobResponse,
  TimelineResponse,
  TimelineUpdateRequest,
} from "../types/timeline.types";

async function listEpisodeTimelines(
  episodeId: number | string,
): Promise<ApiResponse<TimelineListResponse>> {
  return httpClient<TimelineListResponse>(
    `/api/v1/episodes/${episodeId}/timelines`,
  );
}

async function getTimeline(
  timelineId: number | string,
): Promise<ApiResponse<TimelineResponse>> {
  return httpClient<TimelineResponse>(`/api/v1/timelines/${timelineId}`);
}

async function listTimelineClipTasks(
  timelineId: number | string,
): Promise<ApiResponse<TimelineClipTaskListResponse>> {
  return httpClient<TimelineClipTaskListResponse>(
    `/api/v1/timelines/${timelineId}/clip-tasks`,
  );
}

async function listTimelineResolvedVideos(
  timelineId: number | string,
): Promise<ApiResponse<TimelineResolvedVideoListResponse>> {
  return httpClient<TimelineResolvedVideoListResponse>(
    `/api/v1/timelines/${timelineId}/resolved-videos`,
  );
}

async function updateTimeline(
  timelineId: number | string,
  payload: TimelineUpdateRequest,
): Promise<ApiResponse<TimelineResponse>> {
  return httpClient<TimelineResponse>(`/api/v1/timelines/${timelineId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

async function queueTimelineRender(
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

async function listTimelineRenderJobs(
  timelineId: number | string,
): Promise<ApiResponse<TimelineRenderJobListResponse>> {
  return httpClient<TimelineRenderJobListResponse>(
    `/api/v1/timelines/${timelineId}/render-jobs`,
  );
}

async function listTimelineClipAssets(
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

async function reworkTimelineClip(
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

async function queueTimelineClipVideoRework(
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

async function generateTimelineClipStoryboard(
  timelineId: number | string,
  clipId: string,
  payload: TimelineClipStoryboardGenerateRequest,
): Promise<ApiResponse<TimelineClipStoryboardGenerateResponse>> {
  return httpClient<TimelineClipStoryboardGenerateResponse>(
    `/api/v1/timelines/${timelineId}/clips/${encodeURIComponent(
      clipId,
    )}/storyboard/generate`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

async function generateTimelineClipKeyframes(
  timelineId: number | string,
  clipId: string,
  payload: TimelineClipKeyframeGenerateRequest,
): Promise<ApiResponse<TimelineClipKeyframeGenerateResponse>> {
  return httpClient<TimelineClipKeyframeGenerateResponse>(
    `/api/v1/timelines/${timelineId}/clips/${encodeURIComponent(
      clipId,
    )}/keyframes/generate`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export const timelineAPI = {
  listEpisodeTimelines,
  getTimeline,
  updateTimeline,
  queueTimelineRender,
  listTimelineRenderJobs,
  listTimelineClipAssets,
  listTimelineClipTasks,
  listTimelineResolvedVideos,
  reworkTimelineClip,
  queueTimelineClipVideoRework,
  generateTimelineClipStoryboard,
  generateTimelineClipKeyframes,
};
