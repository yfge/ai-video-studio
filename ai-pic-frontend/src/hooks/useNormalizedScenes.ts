"use client";

import { useCallback, useEffect, useState } from "react";
import { storyStructureAPI } from "@/utils/api";
import type { NormalizedScene } from "@/utils/api";

export function useNormalizedScenes(scriptId: number | null) {
  const [normalizedScenes, setNormalizedScenes] = useState<NormalizedScene[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!scriptId) {
      setNormalizedScenes([]);
      setError(null);
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const res = await storyStructureAPI.getNormalizedScenes(scriptId);
      if (res.success && res.data) {
        setNormalizedScenes(res.data);
      } else {
        setNormalizedScenes([]);
        setError(res.error || "加载场景失败");
      }
    } catch (err) {
      console.error("加载场景失败:", err);
      setNormalizedScenes([]);
      setError("加载场景失败");
    } finally {
      setLoading(false);
    }
  }, [scriptId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {
    normalizedScenes,
    normalizedScenesLoading: loading,
    normalizedScenesError: error,
    refreshNormalizedScenes: refresh,
  };
}
