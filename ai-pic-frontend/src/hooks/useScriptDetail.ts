"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { authAPI, scriptAPI, storyStructureAPI } from "@/utils/api";
import type { NormalizedScene, NormalizedShot, SceneBeat, Script, User } from "@/utils/api";
import type { SceneNode } from "@/components/features";
import { isAdmin } from "@/utils/auth";

export type TabId = "overview" | "scenes";

export type ScriptScene = {
  scene_number?: number | string;
  location?: string;
  time?: string;
  description?: string;
  characters?: string[] | string;
  notes?: string;
  [key: string]: unknown;
};

export type ScriptDialogue =
  | {
      scene_number?: number | string;
      character?: string;
      content?: string;
      emotion?: string;
      action?: string;
    }
  | string;

export type ScriptDirection =
  | {
      scene_number?: number | string;
      timing?: string;
      content?: string;
      type?: string;
    }
  | string;

export const TABS: Array<{ id: TabId; name: string; description: string }> = [
  { id: "overview", name: "概览", description: "剧本文本与统计" },
  { id: "scenes", name: "场景", description: "按场景查看对白与指令" },
];

export const formatDate = (value?: string): string => {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
};

export const toSceneNumber = (value: number | string | undefined): number | undefined => {
  if (typeof value === "number") return value;
  if (typeof value === "string") {
    const parsed = parseInt(value, 10);
    return Number.isNaN(parsed) ? undefined : parsed;
  }
  return undefined;
};

const normalizeScenes = (scenes: unknown): ScriptScene[] => {
  if (!Array.isArray(scenes)) return [];
  return scenes.map((scene, index) => {
    if (scene && typeof scene === "object") {
      return scene as ScriptScene;
    }
    return { scene_number: index + 1, description: typeof scene === "string" ? scene : undefined };
  });
};

const normalizeDialogues = (items: unknown): ScriptDialogue[] =>
  Array.isArray(items) ? (items as ScriptDialogue[]) : [];

const normalizeDirections = (items: unknown): ScriptDirection[] =>
  Array.isArray(items) ? (items as ScriptDirection[]) : [];

export interface UseScriptDetailOptions {
  scriptKey: string;
  showAlert: (opts: { message: string; variant: "success" | "error" | "warning" | "info" }) => void;
}

export function useScriptDetail({ scriptKey, showAlert }: UseScriptDetailOptions) {
  // Core state
  const [activeTab, setActiveTab] = useState<TabId>("scenes");
  const [script, setScript] = useState<Script | null>(null);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [structuredScenes, setStructuredScenes] = useState<SceneNode[]>([]);
  const [normalizedScenes, setNormalizedScenes] = useState<NormalizedScene[]>([]);
  const [sceneBeatsMap, setSceneBeatsMap] = useState<Record<number, SceneBeat[]>>({});
  const [sceneShotsMap, setSceneShotsMap] = useState<Record<number, NormalizedShot[]>>({});
  const [structureLoading, setStructureLoading] = useState(false);
  const [structureError, setStructureError] = useState<string | null>(null);
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

  // Load normalized scenes
  useEffect(() => {
    if (!script?.id) return;
    let cancelled = false;
    const loadStructure = async () => {
      try {
        setStructureLoading(true);
        setStructureError(null);
        const res = await storyStructureAPI.getNormalizedScenes(script.id);
        if (cancelled) return;
        if (res.success && Array.isArray(res.data)) {
          setNormalizedScenes(res.data);
        } else {
          setNormalizedScenes([]);
          if (res.error) setStructureError(res.error);
        }
      } catch (error) {
        if (!cancelled) {
          console.error("Failed to load structured scenes", error);
          setStructureError("加载结构化场景失败");
        }
      } finally {
        if (!cancelled) setStructureLoading(false);
      }
    };
    loadStructure();
    return () => {
      cancelled = true;
    };
  }, [script?.id]);

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
  const rawScenes = useMemo(() => normalizeScenes(script?.scenes), [script?.scenes]);

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

  const structuredSceneViews = useMemo<ScriptScene[]>(() => {
    if (!structuredScenes.length) return [];
    return structuredScenes.map((scene, idx) => ({
      scene_number: toSceneNumber(scene.scene_number) ?? idx + 1,
      location: scene.location,
      time: scene.time_of_day,
      description: scene.slug_line || scene.status || `场景 ${scene.scene_number}`,
    }));
  }, [structuredScenes]);

  const scenes = structuredSceneViews.length > 0 ? structuredSceneViews : rawScenes;
  const dialogues = useMemo(() => normalizeDialogues(script?.dialogues), [script?.dialogues]);
  const directions = useMemo(() => normalizeDirections(script?.stage_directions), [script?.stage_directions]);

  const activeScene = useMemo(
    () => (focusedScene ? scenes.find((scene) => toSceneNumber(scene.scene_number) === focusedScene) || null : null),
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

  const selectedNormalizedScene = focusedScene ? normalizedSceneMap.get(focusedScene) : undefined;
  const sceneBeats = selectedNormalizedScene ? sceneBeatsMap[selectedNormalizedScene.id] : undefined;
  const sceneShots = selectedNormalizedScene ? sceneShotsMap[selectedNormalizedScene.id] : undefined;
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
          setSceneBeatsMap((prev) => ({ ...prev, [sceneId]: beatsRes.data as SceneBeat[] }));
        }
        if (shotsRes.success && Array.isArray(shotsRes.data)) {
          setSceneShotsMap((prev) => ({ ...prev, [sceneId]: shotsRes.data as NormalizedShot[] }));
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
        showAlert({ message: `剧本已导出为 ${format.toUpperCase()}`, variant: "success" });
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
