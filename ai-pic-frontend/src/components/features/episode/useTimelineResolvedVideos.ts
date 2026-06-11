"use client";

import { useCallback, useEffect, useState } from "react";
import { timelineAPI } from "@/utils/api/endpoints";
import type {
  TimelineResolvedVideoListResponse,
  TimelineResponse,
} from "@/utils/api/types";

export function useTimelineResolvedVideos({
  selectedTimelineSpec,
  refreshKey,
}: {
  selectedTimelineSpec: TimelineResponse | null;
  refreshKey?: string | number | null;
}) {
  const [resolvedVideos, setResolvedVideos] =
    useState<TimelineResolvedVideoListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadResolvedVideos = useCallback(async () => {
    if (!selectedTimelineSpec?.id) {
      setResolvedVideos(null);
      setError(null);
      return;
    }
    setLoading(true);
    try {
      const res = await timelineAPI.listTimelineResolvedVideos(
        selectedTimelineSpec.id,
      );
      if (res.success && res.data) {
        setResolvedVideos(res.data);
        setError(null);
      } else {
        setError(res.error || "读取片段视频失败");
      }
    } finally {
      setLoading(false);
    }
  }, [selectedTimelineSpec?.id]);

  useEffect(() => {
    void loadResolvedVideos();
  }, [loadResolvedVideos, refreshKey]);

  return {
    resolvedVideos,
    loading,
    error,
    reloadResolvedVideos: loadResolvedVideos,
  };
}
