import { useCallback, useEffect, useMemo, useState } from "react";
import type {
  NormalizedScene,
  NormalizedShot,
  SceneBeat,
  Script,
} from "@/utils/api/types";
import { authAPI, storyStructureAPI } from "@/utils/api/endpoints";
import { isAdmin } from "@/utils/auth";
import type { User } from "@/utils/api/types";
import type { SceneNode } from "../SceneStructurePanel";
import {
  normalizeDialogues,
  normalizeDirections,
  normalizeScenes,
  sceneNodesFromNormalizedScenes,
  sceneViewsFromNodes,
  type ScriptScene,
  toSceneNumber,
} from "./WorkspaceScriptTabContentModel";

export function useWorkspaceScriptStructure(script: Script | null) {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [structuredScenes, setStructuredScenes] = useState<SceneNode[]>([]);
  const [normalizedScenes, setNormalizedScenes] = useState<NormalizedScene[]>([]);
  const [sceneBeatsMap, setSceneBeatsMap] = useState<
    Record<number, SceneBeat[]>
  >({});
  const [sceneShotsMap, setSceneShotsMap] = useState<
    Record<number, NormalizedShot[]>
  >({});
  const [structureLoading, setStructureLoading] = useState(false);
  const [structureError, setStructureError] = useState<string | null>(null);
  const [showStructureEditor, setShowStructureEditor] = useState(false);
  const [focusedScene, setFocusedScene] = useState<number | null>(null);

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
    void loadStructure();
    return () => {
      cancelled = true;
    };
  }, [script?.id]);

  useEffect(() => {
    let mounted = true;
    const loadUser = async () => {
      try {
        const res = await authAPI.getCurrentUser();
        if (mounted && res.success && res.data) setCurrentUser(res.data);
      } catch (error) {
        console.error("Failed to load user info", error);
      }
    };
    void loadUser();
    return () => {
      mounted = false;
    };
  }, []);

  const rawScenes = useMemo(
    () => normalizeScenes(script?.scenes),
    [script?.scenes],
  );

  useEffect(() => {
    if (normalizedScenes.length) {
      setStructuredScenes(sceneNodesFromNormalizedScenes(normalizedScenes));
    }
  }, [normalizedScenes]);

  const structuredSceneViews = useMemo<ScriptScene[]>(
    () => sceneViewsFromNodes(structuredScenes),
    [structuredScenes],
  );
  const scenes = structuredSceneViews.length ? structuredSceneViews : rawScenes;
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
      if (num !== undefined) map.set(num, scene);
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

  useEffect(() => {
    if (!focusedScene && scenes.length > 0) {
      const first = toSceneNumber(scenes[0].scene_number);
      if (first) setFocusedScene(first);
    }
  }, [focusedScene, scenes]);

  return {
    scenes,
    dialogues,
    directions,
    focusedScene,
    setFocusedScene,
    activeScene,
    selectedNormalizedScene,
    sceneBeats,
    sceneShots,
    structureLoading,
    structureError,
    showStructureEditor,
    setShowStructureEditor,
    canEditStructure: isAdmin(currentUser),
    setStructuredScenes,
  };
}
