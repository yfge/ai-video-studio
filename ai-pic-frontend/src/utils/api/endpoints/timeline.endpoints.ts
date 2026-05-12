/**
 * Timeline Spec v1 API endpoints.
 */

import { httpClient } from "../client";
import type { ApiResponse } from "../types/common.types";
import type { TimelineListResponse } from "../types/timeline.types";

export async function listEpisodeTimelines(
  episodeId: number | string,
): Promise<ApiResponse<TimelineListResponse>> {
  return httpClient<TimelineListResponse>(
    `/api/v1/episodes/${episodeId}/timelines`,
  );
}

export const timelineAPI = {
  listEpisodeTimelines,
};
