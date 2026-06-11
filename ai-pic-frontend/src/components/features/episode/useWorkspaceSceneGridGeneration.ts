"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  episodeAPI,
  episodeCharacterAPI,
  generateSceneGridSheet,
  generateSceneGridVideo,
  getSceneGrids,
  storyAPI,
  type SceneGridInfo,
  type SceneGridMap,
} from "@/utils/api/endpoints";
import type { NormalizedScene } from "@/utils/api/types";
import {
  isGenerationTaskActive,
  useGenerationTaskTracker,
} from "@/hooks/useGenerationTaskTracker";

export type SceneGridCharacterOption = {
  key: string;
  virtual_ip_id: number;
  label: string;
};

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
  const [imageModel, setImageModel] = useState("codex:gpt-image-2");
  const [characters, setCharacters] = useState<SceneGridCharacterOption[]>([]);
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
    const load = async () => {
      try {
        const data = await episodeCharacterAPI.listEpisodeCharacters(
          episodeKey,
          { page_size: 50 },
        );
        const episodeOptions = (data?.items || [])
          .filter((item) => item.virtual_ip_id)
          .map((item) => ({
            key: `ep-${item.id}`,
            virtual_ip_id: item.virtual_ip_id,
            label:
              item.character_name ||
              item.display_name ||
              item.name ||
              `角色${item.virtual_ip_id}`,
          }));
        if (episodeOptions.length) {
          setCharacters(episodeOptions);
          return;
        }
      } catch {
        // fall through to story characters
      }
      try {
        const episodeRes = await episodeAPI.getEpisode(episodeKey);
        const storyId = episodeRes.success ? episodeRes.data?.story_id : null;
        if (!storyId) return;
        const charsRes = await storyAPI.getStoryCharacters(storyId);
        if (charsRes.success && charsRes.data) {
          setCharacters(
            charsRes.data
              .filter((item) => item.virtual_ip_id)
              .map((item) => ({
                key: `story-${item.id}`,
                virtual_ip_id: item.virtual_ip_id,
                label:
                  item.character_name ||
                  item.display_name ||
                  item.name ||
                  item.virtual_ip_name ||
                  `角色${item.virtual_ip_id}`,
              })),
          );
        }
      } catch {
        setCharacters([]);
      }
    };
    void load();
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
        return { virtual_ip_id: virtualIpId, name: matched?.label };
      });
      const envRefs = environmentUrls
        .split(/[\n,]/)
        .map((value) => value.trim())
        .filter(Boolean);
      const res = await generateSceneGridSheet(selectedScriptId, {
        scene_number: sceneNumber,
        grid_size: gridSize,
        model: imageModel || undefined,
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
    imageModel,
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
    imageModel,
    setImageModel,
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
