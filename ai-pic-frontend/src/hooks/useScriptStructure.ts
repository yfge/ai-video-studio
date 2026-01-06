"use client";

import { useEffect, useState } from "react";
import { storyStructureAPI } from "@/utils/api";
import type { NormalizedScene } from "@/utils/api";
import type { SceneNode } from "@/components/features";

export function useScriptStructure(scriptId?: number) {
  const [normalizedScenes, setNormalizedScenes] = useState<NormalizedScene[]>([]);
  const [structuredScenes, setStructuredScenes] = useState<SceneNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!scriptId) return;
    let cancelled = false;
    const loadStructure = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await storyStructureAPI.getNormalizedScenes(scriptId);
        if (cancelled) return;
        if (res.success && Array.isArray(res.data)) {
          setNormalizedScenes(res.data);
        } else {
          setNormalizedScenes([]);
          if (res.error) setError(res.error);
        }
      } catch (err) {
        if (!cancelled) {
          console.error("Failed to load structured scenes", err);
          setError("加载结构化场景失败");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    loadStructure();
    return () => {
      cancelled = true;
    };
  }, [scriptId]);

  useEffect(() => {
    if (!normalizedScenes.length) return;
    setStructuredScenes(
      normalizedScenes.map((scene) => ({
        id: scene.id,
        scene_number: scene.scene_number,
        slug_line: scene.slug_line,
        location: scene.location ?? undefined,
        time_of_day: scene.time_of_day ?? undefined,
        status: scene.status,
        beats: [],
        shots: [],
      })),
    );
  }, [normalizedScenes]);

  return {
    normalizedScenes,
    structuredScenes,
    setStructuredScenes,
    structureLoading: loading,
    structureError: error,
  };
}
