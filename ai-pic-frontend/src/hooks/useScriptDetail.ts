"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { authAPI, scriptAPI, storyStructureAPI } from "@/utils/api";
import type {
  NormalizedScene,
  NormalizedShot,
  SceneBeat,
  Script,
  User,
} from "@/utils/api";
import { isAdmin } from "@/utils/auth";
import {
  normalizeDialogues,
  normalizeDirections,
  normalizeScenes,
  toSceneNumber,
  type ScriptScene,
} from "@/hooks/scriptDetailUtils";
import { SCRIPT_TABS, type ScriptTabId } from "@/hooks/scriptTabs";
import { useScriptStructure } from "@/hooks/useScriptStructure";

export type TabId = ScriptTabId;
export const TABS = SCRIPT_TABS;
export { formatDate, toSceneNumber } from "@/hooks/scriptDetailUtils";
export type {
  ScriptScene,
  ScriptDialogue,
  ScriptDirection,
} from "@/hooks/scriptDetailUtils";

export interface UseScriptDetailOptions {
  scriptKey: string;
  showAlert: (opts: {
    message: string;
    variant: "success" | "error" | "warning" | "info";
  }) => void;
}

export function useScriptDetail({
  scriptKey,
  showAlert,
}: UseScriptDetailOptions) {
  // Core state
  const [activeTab, setActiveTab] = useState<TabId>("scenes");
  const [script, setScript] = useState<Script | null>(null);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [sceneBeatsMap, setSceneBeatsMap] = useState<
    Record<number, SceneBeat[]>
  >({});
  const [sceneShotsMap, setSceneShotsMap] = useState<
    Record<number, NormalizedShot[]>
  >({});
  const {
    normalizedScenes,
    structuredScenes,
    setStructuredScenes,
    structureLoading,
    structureError,
  } = useScriptStructure(script?.id);
  const [showStructureEditor, setShowStructureEditor] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [focusedScene, setFocusedScene] = useState<number | null>(null);

  // Load initial data
  const loadInitialData = useCallback(async () => {
    try {
      setLoading(true);
      const scriptRes = await scriptAPI.getScript(scriptKey);
      if (scriptRes.success && scriptRes.data) {
        setScript(scriptRes.data);
      } else {
        showAlert({ message: "加载剧本失败", variant: "error" });
      }
    } catch (error) {
      console.error(error);
      showAlert({ message: "加载数据失败", variant: "error" });
    } finally {
      setLoading(false);
    }
  }, [scriptKey, showAlert]);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Load current user
  useEffect(() => {
    let mounted = true;
    const loadUser = async () => {
      try {
        const res = await authAPI.getCurrentUser();
        if (mounted && res.success && res.data) {
          setCurrentUser(res.data);
        }
      } catch (error) {
        console.error("Failed to load user info", error);
      }
    };
    loadUser();
    return () => {
      mounted = false;
    };
  }, []);

  // Computed values
  const rawScenes = useMemo(
    () => normalizeScenes(script?.scenes),
    [script?.scenes],
  );

  const structuredSceneViews = useMemo<ScriptScene[]>(() => {
    if (!structuredScenes.length) return [];
    return structuredScenes.map((scene, idx) => ({
      scene_number: toSceneNumber(scene.scene_number) ?? idx + 1,
      location: scene.location,
      time: scene.time_of_day,
      description:
        scene.slug_line || scene.status || `场景 ${scene.scene_number}`,
    }));
  }, [structuredScenes]);

  const scenes =
    structuredSceneViews.length > 0 ? structuredSceneViews : rawScenes;
  const dialogues = useMemo(
    () => normalizeDialogues(script?.dialogues),
    [script?.dialogues],
  );
  const directions = useMemo(
    () => normalizeDirections(script?.stage_directions),
    [script?.stage_directions],
  );

  const activeScene = useMemo(
    () =>
      focusedScene
        ? scenes.find(
            (scene) => toSceneNumber(scene.scene_number) === focusedScene,
          ) || null
        : null,
    [focusedScene, scenes],
  );

  const normalizedSceneMap = useMemo(() => {
    const map = new Map<number, NormalizedScene>();
    normalizedScenes.forEach((scene) => {
      const num = toSceneNumber(scene.scene_number);
      if (num !== undefined) {
        map.set(num, scene);
      }
    });
    return map;
  }, [normalizedScenes]);

  const selectedNormalizedScene = focusedScene
    ? normalizedSceneMap.get(focusedScene)
    : undefined;
  const sceneBeats = selectedNormalizedScene
    ? sceneBeatsMap[selectedNormalizedScene.id]
    : undefined;
  const sceneShots = selectedNormalizedScene
    ? sceneShotsMap[selectedNormalizedScene.id]
    : undefined;
  const scriptIdentifier = script?.business_id || scriptKey;
  const canEditStructure = useMemo(() => isAdmin(currentUser), [currentUser]);

  // Load scene structure
  const loadSceneStructure = useCallback(
    async (sceneId: number) => {
      if (sceneBeatsMap[sceneId] && sceneShotsMap[sceneId]) return;
      try {
        const [beatsRes, shotsRes] = await Promise.all([
          storyStructureAPI.getNormalizedSceneBeats(sceneId),
          storyStructureAPI.getNormalizedSceneShots(sceneId),
        ]);
        if (beatsRes.success && Array.isArray(beatsRes.data)) {
          setSceneBeatsMap((prev) => ({
            ...prev,
            [sceneId]: beatsRes.data as SceneBeat[],
          }));
        }
        if (shotsRes.success && Array.isArray(shotsRes.data)) {
          setSceneShotsMap((prev) => ({
            ...prev,
            [sceneId]: shotsRes.data as NormalizedShot[],
          }));
        }
      } catch (error) {
        console.error("Failed to load scene structure", error);
      }
    },
    [sceneBeatsMap, sceneShotsMap],
  );

  useEffect(() => {
    if (selectedNormalizedScene?.id) {
      void loadSceneStructure(selectedNormalizedScene.id);
    }
  }, [loadSceneStructure, selectedNormalizedScene?.id]);

  // Auto-select first scene
  useEffect(() => {
    if (!focusedScene && scenes.length > 0) {
      const first = toSceneNumber(scenes[0].scene_number);
      if (first) setFocusedScene(first);
    }
  }, [focusedScene, scenes]);

  // Event handlers
  const handleExport = async (format: string) => {
    try {
      const response = await scriptAPI.exportScript(scriptIdentifier, format);
      if (response.success) {
        showAlert({
          message: `剧本已导出为 ${format.toUpperCase()}`,
          variant: "success",
        });
      } else {
        showAlert({ message: "导出失败", variant: "error" });
      }
    } catch (error) {
      console.error(error);
      showAlert({ message: "导出失败", variant: "error" });
    } finally {
      setShowExportMenu(false);
    }
  };

  const goToSceneDetails = () => {
    setActiveTab("scenes");
    setShowStructureEditor(false);
  };

  const goToSceneStructure = () => {
    setActiveTab("scenes");
    setShowStructureEditor(true);
    if (selectedNormalizedScene?.id) {
      void loadSceneStructure(selectedNormalizedScene.id);
    }
  };

  return {
    // State
    activeTab,
    setActiveTab,
    script,
    currentUser,
    structuredScenes,
    setStructuredScenes,
    normalizedScenes,
    structureLoading,
    structureError,
    showStructureEditor,
    setShowStructureEditor,
    loading,
    showExportMenu,
    setShowExportMenu,
    focusedScene,
    setFocusedScene,

    // Computed
    scenes,
    dialogues,
    directions,
    activeScene,
    selectedNormalizedScene,
    sceneBeats,
    sceneShots,
    canEditStructure,

    // Handlers
    handleExport,
    goToSceneDetails,
    goToSceneStructure,
  };
}
