"use client";

import { useCallback } from "react";
import { timelineAPI } from "@/utils/api/endpoints";
import type { TimelineResponse } from "@/utils/api/types";

/**
 * Refresh clip assets and re-fetch the timeline spec after a clip generation
 * task completes, so previews and panel references update in place.
 */
export function useTimelineGenerationRefresh({
  timelineSpecId,
  onTimelineUpdated,
  reloadClipAssets,
  reloadRenderJobs,
  reloadResolvedVideos,
}: {
  timelineSpecId: number | string | null;
  onTimelineUpdated?: (timeline: TimelineResponse) => void;
  reloadClipAssets?: () => void | Promise<void>;
  reloadRenderJobs?: () => void | Promise<void>;
  reloadResolvedVideos?: () => void | Promise<void>;
}) {
  return useCallback(
    async (timeline?: TimelineResponse) => {
      if (timeline) {
        onTimelineUpdated?.(timeline);
        return;
      }
      await reloadClipAssets?.();
      await reloadResolvedVideos?.();
      // 片段视频成功后后端会自动排最终渲染，这里刷新渲染面板让新 job 立即可见
      await reloadRenderJobs?.();
      if (!timelineSpecId || !onTimelineUpdated) return;
      const res = await timelineAPI.getTimeline(timelineSpecId);
      if (res.success && res.data) onTimelineUpdated(res.data);
    },
    [
      onTimelineUpdated,
      reloadClipAssets,
      reloadRenderJobs,
      reloadResolvedVideos,
      timelineSpecId,
    ],
  );
}
