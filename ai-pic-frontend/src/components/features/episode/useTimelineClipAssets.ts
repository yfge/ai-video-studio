"use client";

import { useCallback, useEffect, useState } from "react";
import { timelineAPI } from "@/utils/api/endpoints";
import type {
  TimelineClipAssetResponse,
  TimelineResponse,
} from "@/utils/api/types";

export function useTimelineClipAssets({
  selectedTimelineSpec,
  refreshKey,
}: {
  selectedTimelineSpec: TimelineResponse | null;
  refreshKey?: string | number | null;
}) {
  const [clipAssets, setClipAssets] = useState<TimelineClipAssetResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadClipAssets = useCallback(async () => {
    if (!selectedTimelineSpec?.id) {
      setClipAssets([]);
      setError(null);
      return;
    }
    setLoading(true);
    try {
      const res = await timelineAPI.listTimelineClipAssets(
        selectedTimelineSpec.id,
        { timelineVersion: selectedTimelineSpec.version },
      );
      if (res.success && res.data) {
        setClipAssets(res.data.items || []);
        setError(null);
      } else {
        setError(res.error || "读取片段资产失败");
      }
    } finally {
      setLoading(false);
    }
  }, [selectedTimelineSpec?.id, selectedTimelineSpec?.version]);

  useEffect(() => {
    void loadClipAssets();
  }, [loadClipAssets, refreshKey]);

  return {
    clipAssets,
    loading,
    error,
    reloadClipAssets: loadClipAssets,
  };
}
