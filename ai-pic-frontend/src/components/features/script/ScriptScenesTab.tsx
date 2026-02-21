"use client";

import type {
  NormalizedScene,
  NormalizedShot,
  SceneBeat,
  Script,
} from "@/utils/api/types";
import type {
  ScriptScene,
  ScriptDialogue,
  ScriptDirection,
} from "@/hooks/useScriptDetail";
import { toSceneNumber } from "@/hooks/useScriptDetail";
import { SceneStructurePanel, type SceneNode } from "@/components/features";
import { formatText } from "@/components/features/StoryboardFrameCard";

interface ScriptScenesTabProps {
  script: Script;
  scenes: ScriptScene[];
  dialogues: ScriptDialogue[];
  directions: ScriptDirection[];
  focusedScene: number | null;
  setFocusedScene: (scene: number) => void;
  activeScene: ScriptScene | null;
  selectedNormalizedScene: NormalizedScene | undefined;
  sceneBeats: SceneBeat[] | undefined;
  sceneShots: NormalizedShot[] | undefined;
  structureLoading: boolean;
  structureError: string | null;
  showStructureEditor: boolean;
  setShowStructureEditor: (show: boolean) => void;
  canEditStructure: boolean;
  setStructuredScenes: (scenes: SceneNode[]) => void;
}

export function ScriptScenesTab({
  script,
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
  canEditStructure,
  setStructuredScenes,
}: ScriptScenesTabProps) {
  const getSceneDialogueCount = (sceneNumber: number | undefined) => {
    if (!sceneNumber) return 0;
    return dialogues.filter((item) => {
      if (typeof item === "string") return false;
      return toSceneNumber(item.scene_number) === sceneNumber;
    }).length;
  };

  const getSceneCharacters = (scene: ScriptScene): string[] => {
    if (!scene.characters) return [];
    if (Array.isArray(scene.characters)) return scene.characters;
    return String(scene.characters)
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  };

  return (
    <div className="flex h-[calc(100vh-320px)] min-h-[500px] gap-4">
      {/* Left sidebar - Scene list */}
      <div className="w-80 flex-shrink-0 rounded-xl bg-white shadow overflow-hidden flex flex-col">
        <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
          <h3 className="font-semibold text-gray-900">场景列表</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            共 {scenes.length} 个场景
          </p>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-2">
          {scenes.length === 0 && (
            <p className="text-sm text-gray-500 p-4 text-center">
              暂无场景数据
            </p>
          )}
          {scenes.map((scene, idx) => {
            const sceneNumber = toSceneNumber(scene.scene_number) ?? idx + 1;
            const isActive = focusedScene === sceneNumber;
            const dialogueCount = getSceneDialogueCount(sceneNumber);
            const characters = getSceneCharacters(scene);

            return (
              <button
                key={`scene-nav-${sceneNumber}`}
                onClick={() => setFocusedScene(sceneNumber)}
                className={`w-full rounded-lg border p-3 text-left transition-all ${
                  isActive
                    ? "border-blue-500 bg-blue-50 ring-1 ring-blue-500"
                    : "border-gray-200 bg-white hover:border-blue-300 hover:bg-gray-50"
                }`}
              >
                {/* Scene header */}
                <div className="flex items-center justify-between">
                  <span
                    className={`text-sm font-semibold ${
                      isActive ? "text-blue-700" : "text-gray-900"
                    }`}
                  >
                    场景 {sceneNumber}
                  </span>
                  {scene.time && (
                    <span
                      className={`text-xs px-2 py-0.5 rounded ${
                        isActive
                          ? "bg-blue-100 text-blue-600"
                          : "bg-gray-100 text-gray-500"
                      }`}
                    >
                      {scene.time}
                    </span>
                  )}
                </div>

                {/* Location */}
                {scene.location && (
                  <div
                    className={`mt-1.5 text-xs ${
                      isActive ? "text-blue-600" : "text-gray-600"
                    }`}
                  >
                    📍 {scene.location}
                  </div>
                )}

                {/* Description */}
                <p
                  className={`mt-2 text-xs leading-relaxed line-clamp-2 ${
                    isActive ? "text-blue-700" : "text-gray-500"
                  }`}
                >
                  {formatText(scene.description, "暂无描述", 80)}
                </p>

                {/* Stats row */}
                <div className="mt-2 flex items-center gap-3 text-[11px]">
                  {characters.length > 0 && (
                    <span
                      className={isActive ? "text-blue-500" : "text-gray-400"}
                    >
                      👤 {characters.length} 角色
                    </span>
                  )}
                  {dialogueCount > 0 && (
                    <span
                      className={isActive ? "text-blue-500" : "text-gray-400"}
                    >
                      💬 {dialogueCount} 对白
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Right panel - Scene details */}
      <div className="flex-1 rounded-xl bg-white shadow overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto">
          {activeScene ? (
            <SceneDetailPanel
              scene={activeScene}
              dialogues={dialogues}
              directions={directions}
              normalizedScene={selectedNormalizedScene}
              beats={sceneBeats}
              shots={sceneShots}
              structureLoading={structureLoading}
              structureError={structureError}
              showStructureEditor={showStructureEditor}
              setShowStructureEditor={setShowStructureEditor}
              canEditStructure={canEditStructure}
              scriptId={script.id}
              setStructuredScenes={setStructuredScenes}
            />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400">
              <p>请在左侧选择一个场景</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface SceneDetailPanelProps {
  scene: ScriptScene;
  dialogues: ScriptDialogue[];
  directions: ScriptDirection[];
  normalizedScene: NormalizedScene | undefined;
  beats: SceneBeat[] | undefined;
  shots: NormalizedShot[] | undefined;
  structureLoading: boolean;
  structureError: string | null;
  showStructureEditor: boolean;
  setShowStructureEditor: (show: boolean) => void;
  canEditStructure: boolean;
  scriptId: number;
  setStructuredScenes: (scenes: SceneNode[]) => void;
}

function SceneDetailPanel({
  scene,
  dialogues,
  directions,
  normalizedScene,
  beats,
  shots,
  structureLoading,
  structureError,
  showStructureEditor,
  setShowStructureEditor,
  canEditStructure,
  scriptId,
  setStructuredScenes,
}: SceneDetailPanelProps) {
  const sceneNumber = toSceneNumber(scene.scene_number);
  const sceneDialogues = dialogues.filter((item) => {
    if (typeof item === "string") return true;
    return toSceneNumber(item.scene_number) === sceneNumber;
  });
  const sceneDirections = directions.filter((item) => {
    if (typeof item === "string") return true;
    return toSceneNumber(item.scene_number) === sceneNumber;
  });
  const characters = scene.characters
    ? Array.isArray(scene.characters)
      ? scene.characters
      : String(scene.characters)
          .split(",")
          .map((s) => s.trim())
    : [];

  return (
    <div className="p-6 space-y-6">
      {/* Scene header */}
      <div className="border-b border-gray-100 pb-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl font-bold text-gray-900">
            场景 {sceneNumber}
          </span>
          {scene.time && (
            <span className="px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-sm font-medium">
              {scene.time}
            </span>
          )}
        </div>
        {scene.location && (
          <p className="mt-2 text-gray-600 flex items-center gap-2">
            <span className="text-gray-400">📍</span>
            <span className="font-medium">{scene.location}</span>
          </p>
        )}
      </div>

      {/* Description */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-700 mb-2">场景描述</h4>
        <p className="text-gray-600 leading-relaxed">
          {scene.description || "暂无描述"}
        </p>
        {scene.notes && (
          <p className="mt-3 text-sm text-gray-500 border-t border-gray-200 pt-3">
            <span className="font-medium">备注：</span>
            {scene.notes}
          </p>
        )}
      </div>

      {/* Characters */}
      {characters.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-2">出场角色</h4>
          <div className="flex flex-wrap gap-2">
            {characters.map((char, idx) => (
              <span
                key={`char-${idx}`}
                className="px-3 py-1.5 bg-purple-50 text-purple-700 rounded-full text-sm font-medium"
              >
                {char}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Dialogues and Directions grid */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Dialogues */}
        <div className="bg-white border border-gray-200 rounded-lg">
          <div className="px-4 py-3 border-b border-gray-100 bg-gray-50 rounded-t-lg">
            <h4 className="text-sm font-semibold text-gray-700">
              对白
              <span className="ml-2 text-xs font-normal text-gray-400">
                {sceneDialogues.length} 条
              </span>
            </h4>
          </div>
          <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
            {sceneDialogues.length === 0 && (
              <p className="text-sm text-gray-400 text-center py-4">暂无对白</p>
            )}
            {sceneDialogues.map((dialogue, idx) => (
              <div
                key={`dialogue-${idx}`}
                className="bg-gray-50 rounded-lg p-3"
              >
                {typeof dialogue === "string" ? (
                  <p className="text-sm text-gray-600">{dialogue}</p>
                ) : (
                  <>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-gray-800 text-sm">
                        {dialogue.character || "角色"}
                      </span>
                      {dialogue.emotion && (
                        <span className="text-xs px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded">
                          {dialogue.emotion}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600">
                      {dialogue.content || "..."}
                    </p>
                    {dialogue.action && (
                      <p className="text-xs text-gray-400 mt-1 italic">
                        ({dialogue.action})
                      </p>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Directions */}
        <div className="bg-white border border-gray-200 rounded-lg">
          <div className="px-4 py-3 border-b border-gray-100 bg-gray-50 rounded-t-lg">
            <h4 className="text-sm font-semibold text-gray-700">
              舞台指令
              <span className="ml-2 text-xs font-normal text-gray-400">
                {sceneDirections.length} 条
              </span>
            </h4>
          </div>
          <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
            {sceneDirections.length === 0 && (
              <p className="text-sm text-gray-400 text-center py-4">
                暂无舞台指令
              </p>
            )}
            {sceneDirections.map((direction, idx) => (
              <div
                key={`direction-${idx}`}
                className="bg-gray-50 rounded-lg p-3"
              >
                {typeof direction === "string" ? (
                  <p className="text-sm text-gray-600">{direction}</p>
                ) : (
                  <>
                    {direction.type && (
                      <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded mb-1 inline-block">
                        {direction.type}
                      </span>
                    )}
                    <p className="text-sm text-gray-600">
                      {direction.content || "..."}
                    </p>
                    {direction.timing && (
                      <p className="text-xs text-gray-400 mt-1">
                        时机：{direction.timing}
                      </p>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Structure info */}
      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="px-4 py-3 border-b border-gray-100 bg-gray-50 rounded-t-lg flex items-center justify-between">
          <div>
            <h4 className="text-sm font-semibold text-gray-700">结构化信息</h4>
            <p className="text-xs text-gray-500 mt-0.5">
              节拍 {beats?.length ?? 0} · 镜头 {shots?.length ?? 0}
              {structureLoading && " · 加载中..."}
              {structureError && ` · ${structureError}`}
            </p>
          </div>
          <button
            onClick={() => setShowStructureEditor(!showStructureEditor)}
            className="px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-100 transition"
          >
            {showStructureEditor ? "收起" : "编辑结构"}
          </button>
        </div>

        {normalizedScene ? (
          <div className="p-4">
            <div className="grid gap-4 md:grid-cols-2">
              {/* Beats */}
              <div className="bg-gray-50 rounded-lg p-3">
                <h5 className="text-xs font-semibold text-gray-600 mb-2">
                  节拍
                </h5>
                <div className="space-y-2">
                  {(beats ?? []).length === 0 && (
                    <p className="text-xs text-gray-400">暂无节拍</p>
                  )}
                  {(beats ?? []).slice(0, 5).map((beat) => (
                    <div
                      key={beat.id}
                      className="bg-white rounded px-3 py-2 shadow-sm"
                    >
                      <span className="text-xs font-semibold text-blue-600">
                        #{beat.order_index}
                      </span>
                      <p className="text-xs text-gray-600 mt-0.5">
                        {beat.beat_summary || beat.dialogue_excerpt || "—"}
                      </p>
                    </div>
                  ))}
                  {(beats ?? []).length > 5 && (
                    <p className="text-xs text-gray-400">
                      还有 {(beats?.length ?? 0) - 5} 个节拍...
                    </p>
                  )}
                </div>
              </div>

              {/* Shots */}
              <div className="bg-gray-50 rounded-lg p-3">
                <h5 className="text-xs font-semibold text-gray-600 mb-2">
                  镜头
                </h5>
                <div className="space-y-2">
                  {(shots ?? []).length === 0 && (
                    <p className="text-xs text-gray-400">暂无镜头</p>
                  )}
                  {(shots ?? []).slice(0, 5).map((shot) => (
                    <div
                      key={shot.id}
                      className="bg-white rounded px-3 py-2 shadow-sm"
                    >
                      <span className="text-xs font-semibold text-purple-600">
                        镜头 {shot.shot_number}
                      </span>
                      <p className="text-xs text-gray-600 mt-0.5">
                        {shot.shot_type || "未标注"}
                      </p>
                    </div>
                  ))}
                  {(shots ?? []).length > 5 && (
                    <p className="text-xs text-gray-400">
                      还有 {(shots?.length ?? 0) - 5} 个镜头...
                    </p>
                  )}
                </div>
              </div>
            </div>

            {showStructureEditor && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <SceneStructurePanel
                  scriptId={scriptId}
                  canEdit={canEditStructure}
                  onStructureLoaded={setStructuredScenes}
                />
              </div>
            )}
          </div>
        ) : (
          <div className="p-4">
            <p className="text-sm text-gray-400 text-center">
              未找到匹配的结构化场景数据
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
