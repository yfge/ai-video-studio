"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  episodeCharacterAPI,
  generateSceneGridSheet,
  generateSceneGridVideo,
  getSceneGrids,
  type SceneGridInfo,
  type SceneGridMap,
} from "@/utils/api/endpoints";
import type { EpisodeCharacter, NormalizedScene } from "@/utils/api/types";
import {
  isGenerationTaskActive,
  useGenerationTaskTracker,
} from "@/hooks/useGenerationTaskTracker";

type ShowAlert = (options: {
  message: string;
  variant: "info" | "success" | "warning" | "error";
}) => void;

export function useWorkspaceSceneGridGeneration({
  episodeKey,
  selectedScriptId,
  normalizedScenes,
  showAlert,
}: {
  episodeKey?: string;
  selectedScriptId?: number | null;
  normalizedScenes: NormalizedScene[];
  showAlert?: ShowAlert;
}) {
  const [expanded, setExpanded] = useState(false);
  const [grids, setGrids] = useState<SceneGridMap>({});
  const [sceneNumber, setSceneNumber] = useState<number | null>(null);
  const [gridSize, setGridSize] = useState(12);
  const [characters, setCharacters] = useState<EpisodeCharacter[]>([]);
  const [selectedIpIds, setSelectedIpIds] = useState<number[]>([]);
  const [environmentUrls, setEnvironmentUrls] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const sceneNumbers = useMemo(
    () =>
      normalizedScenes
        .map((scene) => Number(scene.scene_number))
        .filter((value) => Number.isFinite(value)),
    [normalizedScenes],
  );

  const refreshGrids = useCallback(async () => {
    if (!selectedScriptId) return;
    try {
      const res = await getSceneGrids(selectedScriptId);
      if (res.success && res.data) {
        setGrids(res.data.scene_grids || {});
      }
    } catch {
      // keep previous grids; transient fetch errors surface on next refresh
    }
  }, [selectedScriptId]);

  useEffect(() => {
    if (expanded) void refreshGrids();
  }, [expanded, refreshGrids]);

  useEffect(() => {
    if (sceneNumber == null && sceneNumbers.length) {
      setSceneNumber(sceneNumbers[0]);
    }
  }, [sceneNumber, sceneNumbers]);

  useEffect(() => {
    if (!expanded || !episodeKey) return;
    episodeCharacterAPI
      .listEpisodeCharacters(episodeKey, { page_size: 50 })
      .then((data) => setCharacters(data?.items || []))
      .catch(() => setCharacters([]));
  }, [expanded, episodeKey]);

  const { tasks, track } = useGenerationTaskTracker<"sheet" | "video">({
    labels: { sheet: "宫格分镜图生成", video: "宫格成片生成" },
    onCompleted: async () => {
      await refreshGrids();
    },
    onNotify: (message, variant) => showAlert?.({ message, variant }),
  });

  const sheetActive = isGenerationTaskActive(tasks.sheet);
  const videoActive = isGenerationTaskActive(tasks.video);
  const currentGrid: SceneGridInfo | undefined =
    sceneNumber != null ? grids[String(sceneNumber)] : undefined;

  const handleGenerateSheet = useCallback(async () => {
    if (!selectedScriptId || sceneNumber == null) return;
    setSubmitting(true);
    try {
      const characterRefs = selectedIpIds.map((virtualIpId) => {
        const matched = characters.find(
          (character) => character.virtual_ip_id === virtualIpId,
        );
        return {
          virtual_ip_id: virtualIpId,
          name:
            matched?.character_name ||
            matched?.display_name ||
            matched?.name ||
            undefined,
        };
      });
      const envRefs = environmentUrls
        .split(/[\n,]/)
        .map((value) => value.trim())
        .filter(Boolean);
      const res = await generateSceneGridSheet(selectedScriptId, {
        scene_number: sceneNumber,
        grid_size: gridSize,
        character_refs: characterRefs,
        environment_refs: envRefs,
      });
      if (res.success && res.data) {
        track("sheet", res.data.task_id);
        showAlert?.({
          message: `宫格分镜图任务已提交 #${res.data.task_id}`,
          variant: "success",
        });
      } else {
        showAlert?.({
          message: res.error || "宫格分镜图任务提交失败",
          variant: "error",
        });
      }
    } finally {
      setSubmitting(false);
    }
  }, [
    characters,
    environmentUrls,
    gridSize,
    sceneNumber,
    selectedIpIds,
    selectedScriptId,
    showAlert,
    track,
  ]);

  const handleGenerateVideo = useCallback(async () => {
    if (!selectedScriptId || sceneNumber == null) return;
    setSubmitting(true);
    try {
      const res = await generateSceneGridVideo(selectedScriptId, {
        scene_number: sceneNumber,
      });
      if (res.success && res.data) {
        track("video", res.data.task_id);
        showAlert?.({
          message: `宫格成片任务已提交 #${res.data.task_id}`,
          variant: "success",
        });
      } else {
        showAlert?.({
          message: res.error || "宫格成片任务提交失败",
          variant: "error",
        });
      }
    } finally {
      setSubmitting(false);
    }
  }, [sceneNumber, selectedScriptId, showAlert, track]);

  return {
    expanded,
    setExpanded,
    grids,
    sceneNumber,
    setSceneNumber,
    sceneNumbers,
    gridSize,
    setGridSize,
    characters,
    selectedIpIds,
    setSelectedIpIds,
    environmentUrls,
    setEnvironmentUrls,
    submitting,
    sheetActive,
    videoActive,
    currentGrid,
    handleGenerateSheet,
    handleGenerateVideo,
  };
}
