"use client";

import { useCallback } from "react";
import { timelineAPI } from "@/utils/api/endpoints";
import type { TimelineResponse } from "@/utils/api/types";
import { useToast } from "@/components/shared/notifications";
import { useGenerationTaskTracker } from "@/hooks/useGenerationTaskTracker";

/**
 * Track the one-click timeline pipeline task and refresh the timeline spec
 * for the current script when the pipeline finishes.
 */
export function useTimelinePipelineTracking(args: {
  episodeId: number | string | null;
  selectedScriptId: number | null;
  onTimelineUpdated?: (timeline: TimelineResponse) => void;
  pollIntervalMs?: number;
}) {
  const { episodeId, selectedScriptId, onTimelineUpdated, pollIntervalMs } =
    args;
  const { notify } = useToast();

  const handleCompleted = useCallback(async () => {
    if (!episodeId || !onTimelineUpdated) return;
    const res = await timelineAPI.listEpisodeTimelines(episodeId);
    if (!res.success || !res.data) return;
    const matched =
      res.data.items.find((item) => item.script_id === selectedScriptId) ??
      null;
    if (matched) onTimelineUpdated(matched);
  }, [episodeId, onTimelineUpdated, selectedScriptId]);

  const tracker = useGenerationTaskTracker<"pipeline">({
    labels: { pipeline: "时间轴流水线" },
    onCompleted: handleCompleted,
    onNotify: notify,
    pollIntervalMs,
    // 流水线包含配音/时间轴/分镜多个阶段，给更长的轮询上限
    maxPollMs: 30 * 60 * 1000,
  });

  const { track } = tracker;
  const trackPipelineTask = useCallback(
    (taskId: number) => track("pipeline", taskId),
    [track],
  );

  return {
    pipelineTask: tracker.tasks.pipeline ?? null,
    trackPipelineTask,
  };
}
