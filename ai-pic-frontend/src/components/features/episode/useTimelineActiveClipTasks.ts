"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { timelineAPI } from "@/utils/api/endpoints";
import type { TimelineClipTaskItem, TimelineResponse } from "@/utils/api/types";
import { buildTimelineRenderReadiness } from "./EpisodeTimelineRenderModel";

const POLL_INTERVAL_MS = 10000;

/**
 * Poll the caller's in-flight generation tasks for the selected timeline and
 * fold them into render readiness, so clips already being produced show as
 * "生成中" instead of "缺失".
 */
export function useTimelineRenderReadinessWithTasks({
  selectedTimelineSpec,
  selectedStoryboard,
}: {
  selectedTimelineSpec: TimelineResponse | null;
  selectedStoryboard: Record<string, unknown> | null;
}) {
  const [items, setItems] = useState<TimelineClipTaskItem[]>([]);
  const timelineId = selectedTimelineSpec?.id ?? null;

  const reload = useCallback(async () => {
    if (!timelineId) {
      setItems([]);
      return;
    }
    const res = await timelineAPI.listTimelineClipTasks(timelineId);
    if (res.success && res.data) setItems(res.data.items || []);
  }, [timelineId]);

  useEffect(() => {
    void reload();
    if (!timelineId) return;
    const timer = setInterval(() => void reload(), POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [reload, timelineId]);

  const activeClipTaskIds = useMemo(() => {
    const ids = new Set<string>();
    for (const item of items) {
      if (item.clip_id) ids.add(item.clip_id);
    }
    return ids;
  }, [items]);

  const renderReadiness = useMemo(
    () =>
      buildTimelineRenderReadiness(
        selectedTimelineSpec,
        selectedStoryboard,
        activeClipTaskIds,
      ),
    [activeClipTaskIds, selectedStoryboard, selectedTimelineSpec],
  );

  return { renderReadiness, reloadActiveClipTasks: reload };
}
