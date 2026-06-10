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
}: {
  timelineSpecId: number | string | null;
  onTimelineUpdated?: (timeline: TimelineResponse) => void;
  reloadClipAssets?: () => void | Promise<void>;
}) {
  return useCallback(async () => {
    await reloadClipAssets?.();
    if (!timelineSpecId || !onTimelineUpdated) return;
    const res = await timelineAPI.getTimeline(timelineSpecId);
    if (res.success && res.data) onTimelineUpdated(res.data);
  }, [onTimelineUpdated, reloadClipAssets, timelineSpecId]);
}
