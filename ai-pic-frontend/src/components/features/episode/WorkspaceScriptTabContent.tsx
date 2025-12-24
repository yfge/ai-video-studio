"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { NormalizedScene, NormalizedShot, SceneBeat, Script, ScriptGenerationRequest } from "@/utils/api";
import { storyStructureAPI, authAPI } from "@/utils/api";
import { ScriptOverviewTab, ScriptScenesTab, ScriptGenerationForm } from "@/components/features";
import type { SceneNode } from "@/components/features";
import { isAdmin } from "@/utils/auth";
import type { User } from "@/utils/api";
import { ModelSelector } from "@/components/shared/ModelSelector";

type ScriptScene = {
  scene_number?: number | string;
  location?: string;
  time?: string;
  description?: string;
  characters?: string[] | string;
  notes?: string;
  [key: string]: unknown;
};

type ScriptDialogue =
  | {
      scene_number?: number | string;
      character?: string;
      content?: string;
      emotion?: string;
      action?: string;
    }
  | string;

type ScriptDirection =
  | {
      scene_number?: number | string;
      timing?: string;
      content?: string;
      type?: string;
    }
  | string;

const toSceneNumber = (value: number | string | undefined): number | undefined => {
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

interface WorkspaceScriptTabContentProps {
  script: Script | null;
  // Script generation props
  generateForm: ScriptGenerationRequest;
  setGenerateForm: React.Dispatch<React.SetStateAction<ScriptGenerationRequest>>;
  formats: Array<{ value: string; label: string }>;
  languages: Array<{ value: string; label: string }>;
  useAsync: boolean;
  setUseAsync: (value: boolean) => void;
  promptPreview: string | null;
  setPromptPreview: (value: string | null) => void;
  generating: boolean;
  onGenerate: () => void;
  // Regeneration
  onRegenerateScript?: (model?: string) => void;
  regenerating?: boolean;
}

export function WorkspaceScriptTabContent({
  script,
  generateForm,
  setGenerateForm,
  formats,
  languages,
  useAsync,
  setUseAsync,
  promptPreview,
  setPromptPreview,
  generating,
  onGenerate,
  onRegenerateScript,
  regenerating,
}: WorkspaceScriptTabContentProps) {
  const [activeSubTab, setActiveSubTab] = useState<"overview" | "scenes">("scenes");
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [structuredScenes, setStructuredScenes] = useState<SceneNode[]>([]);
  const [normalizedScenes, setNormalizedScenes] = useState<NormalizedScene[]>([]);
  const [sceneBeatsMap, setSceneBeatsMap] = useState<Record<number, SceneBeat[]>>({});
  const [sceneShotsMap, setSceneShotsMap] = useState<Record<number, NormalizedShot[]>>({});
  const [structureLoading, setStructureLoading] = useState(false);
  const [structureError, setStructureError] = useState<string | null>(null);
  const [showStructureEditor, setShowStructureEditor] = useState(false);
  const [focusedScene, setFocusedScene] = useState<number | null>(null);
  // Regeneration modal state
  const [showRegenerateModal, setShowRegenerateModal] = useState(false);
  const [regenerateModel, setRegenerateModel] = useState<string>("");

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

  if (!script) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">生成剧本</h3>
        <p className="text-gray-500 mb-6">请配置参数并生成剧本以继续工作流</p>
        <ScriptGenerationForm
          generateForm={generateForm}
          setGenerateForm={setGenerateForm}
          formats={formats}
          languages={languages}
          useAsync={useAsync}
          setUseAsync={setUseAsync}
          promptPreview={promptPreview}
          setPromptPreview={setPromptPreview}
          generating={generating}
          onGenerate={onGenerate}
          onCancel={() => {}}
        />
      </div>
    );
  }

  const subTabs = [
    { id: "overview" as const, name: "概览" },
    { id: "scenes" as const, name: "场景" },
  ];

  return (
    <div className="space-y-4">
      {/* Header with sub-tabs and actions */}
      <div className="flex items-center justify-between">
        {/* Sub-tab navigation */}
        <nav className="flex flex-wrap gap-2">
          {subTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id)}
              className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                activeSubTab === tab.id
                  ? "border-blue-600 bg-blue-50 text-blue-700"
                  : "border-gray-200 bg-white text-gray-600 hover:border-blue-200"
              }`}
            >
              {tab.name}
            </button>
          ))}
        </nav>

        {/* Action buttons */}
        {onRegenerateScript && (
          <button
            onClick={() => setShowRegenerateModal(true)}
            disabled={regenerating}
            className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition ${
              regenerating
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : "bg-amber-500 text-white hover:bg-amber-600"
            }`}
          >
            {regenerating ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                重新生成中...
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                重新生成剧本
              </>
            )}
          </button>
        )}
      </div>

      {/* Regeneration Modal */}
      {showRegenerateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">重新生成剧本</h3>
            <p className="text-sm text-gray-600 mb-4">
              重新生成将使用AI创建新的剧本内容，并应用最新的分类优化。
            </p>
            <ModelSelector
              value={regenerateModel}
              onChange={setRegenerateModel}
              label="选择模型"
              helperText="留空使用原有模型设置"
              allowAuto={true}
              autoLabel="使用原有模型"
              modelType="text"
            />
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => {
                  setShowRegenerateModal(false);
                  setRegenerateModel("");
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                取消
              </button>
              <button
                onClick={() => {
                  setShowRegenerateModal(false);
                  onRegenerateScript(regenerateModel || undefined);
                  setRegenerateModel("");
                }}
                disabled={regenerating}
                className="px-4 py-2 text-sm font-medium text-white bg-amber-500 rounded-lg hover:bg-amber-600 disabled:bg-gray-300"
              >
                确认重新生成
              </button>
            </div>
          </div>
        </div>
      )}

      {activeSubTab === "overview" && (
        <ScriptOverviewTab
          script={script}
          scenes={scenes}
          dialogues={dialogues}
          directions={directions}
        />
      )}

      {activeSubTab === "scenes" && (
        <ScriptScenesTab
          script={script}
          scenes={scenes}
          dialogues={dialogues}
          directions={directions}
          focusedScene={focusedScene}
          setFocusedScene={setFocusedScene}
          activeScene={activeScene}
          selectedNormalizedScene={selectedNormalizedScene}
          sceneBeats={sceneBeats}
          sceneShots={sceneShots}
          structureLoading={structureLoading}
          structureError={structureError}
          showStructureEditor={showStructureEditor}
          setShowStructureEditor={setShowStructureEditor}
          canEditStructure={canEditStructure}
          setStructuredScenes={setStructuredScenes}
        />
      )}
    </div>
  );
}
