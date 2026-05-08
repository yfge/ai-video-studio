"use client";

import type {
  NormalizedScene,
  NormalizedShot,
  SceneBeat,
  Script,
} from "@/utils/api/types";
import type {
  ScriptDialogue,
  ScriptDirection,
  ScriptScene,
} from "@/hooks/useScriptDetail";
import { toSceneNumber } from "@/hooks/useScriptDetail";
import { formatText } from "@/components/features/StoryboardFrameCard";
import {
  OperatorContextRail,
  OperatorInspector,
  OperatorListRow,
  OperatorMainCanvas,
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
  OperatorWorkspace,
  StatusPill,
  operatorButtonClass,
} from "@/components/shared";
import { SceneStructurePanel, type SceneNode } from "../SceneStructurePanel";

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

export function ScriptScenesTab(props: ScriptScenesTabProps) {
  const activeNumber = toSceneNumber(props.activeScene?.scene_number);
  const sceneDialogues = filterByScene(props.dialogues, activeNumber);
  const sceneDirections = filterByScene(props.directions, activeNumber);

  return (
    <OperatorWorkspace
      variant="rail-main-inspector"
      className="h-[calc(100vh-18rem)] min-h-[560px]"
      rail={
        <OperatorContextRail title="场景列表" subtitle={`共 ${props.scenes.length} 个`}>
          <div className="space-y-2">
            {props.scenes.map((scene, index) => {
              const sceneNumber = toSceneNumber(scene.scene_number) ?? index + 1;
              return (
                <OperatorListRow
                  key={`${sceneNumber}-${index}`}
                  selected={props.focusedScene === sceneNumber}
                  onClick={() => props.setFocusedScene(sceneNumber)}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium text-gray-950">
                      场景 {sceneNumber}
                    </span>
                    <StatusPill tone="gray">
                      {filterByScene(props.dialogues, sceneNumber).length} 句
                    </StatusPill>
                  </div>
                  <p className="mt-1 line-clamp-2 text-xs text-gray-500">
                    {formatText(scene.description, "暂无描述", 100)}
                  </p>
                </OperatorListRow>
              );
            })}
          </div>
        </OperatorContextRail>
      }
      main={
        <OperatorMainCanvas className="space-y-4">
          <OperatorPanel>
            <OperatorSectionHeader
              title={props.activeScene ? `场景 ${activeNumber || ""}` : "场景详情"}
              subtitle={props.activeScene?.location || "选择左侧场景查看详情"}
            />
            <div className="space-y-4 p-4">
              {props.activeScene ? (
                <>
                  <p className="text-sm leading-6 text-gray-700">
                    {formatText(props.activeScene.description, "暂无场景描述", 500)}
                  </p>
                  <ContentBlock title="对白" items={sceneDialogues} empty="暂无对白" />
                  <ContentBlock title="舞台指令" items={sceneDirections} empty="暂无舞台指令" />
                </>
              ) : (
                <OperatorState title="请选择场景" detail="左侧列表用于定位剧本场景。" />
              )}
            </div>
          </OperatorPanel>
        </OperatorMainCanvas>
      }
      inspector={
        <OperatorInspector
          title="结构检查"
          subtitle="节拍、镜头和规范化场景"
          action={
            <button
              type="button"
              onClick={() => props.setShowStructureEditor(!props.showStructureEditor)}
              className={operatorButtonClass("secondary")}
            >
              {props.showStructureEditor ? "收起" : "编辑"}
            </button>
          }
        >
          {props.structureLoading ? <OperatorState title="加载结构化场景..." /> : null}
          {props.structureError ? <OperatorState title={props.structureError} tone="red" /> : null}
          <StructureSummary
            scene={props.selectedNormalizedScene}
            beats={props.sceneBeats}
            shots={props.sceneShots}
          />
          {props.showStructureEditor ? (
            <div className="mt-4">
              <SceneStructurePanel
                scriptId={props.script.id}
                canEdit={props.canEditStructure}
                onStructureLoaded={props.setStructuredScenes}
              />
            </div>
          ) : null}
        </OperatorInspector>
      }
    />
  );
}

function filterByScene<T extends string | { scene_number?: unknown }>(
  items: T[],
  sceneNumber?: number,
) {
  if (!sceneNumber) return [];
  return items.filter((item) => {
    if (typeof item === "string") return false;
    const candidate = item.scene_number;
    return toSceneNumber(
      typeof candidate === "string" || typeof candidate === "number"
        ? candidate
        : undefined,
    ) === sceneNumber;
  });
}

function ContentBlock({
  title,
  items,
  empty,
}: {
  title: string;
  items: Array<string | { character?: string; content?: string }>;
  empty: string;
}) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-800">{title}</h3>
      <div className="mt-2 space-y-2">
        {items.length ? (
          items.map((item, index) => (
            <div key={index} className="rounded-md border border-gray-200 bg-gray-50 p-3 text-xs text-gray-700">
              {typeof item === "string" ? item : `${item.character || "角色"}：${item.content || ""}`}
            </div>
          ))
        ) : (
          <div className="rounded-md border border-gray-200 bg-gray-50 p-3 text-xs text-gray-500">
            {empty}
          </div>
        )}
      </div>
    </div>
  );
}

function StructureSummary({
  scene,
  beats,
  shots,
}: {
  scene?: NormalizedScene;
  beats?: SceneBeat[];
  shots?: NormalizedShot[];
}) {
  if (!scene) {
    return <OperatorState title="未匹配规范化场景" tone="amber" />;
  }
  return (
    <div className="space-y-3">
      <div className="rounded-md border border-gray-200 bg-gray-50 p-3">
        <div className="text-sm font-medium text-gray-950">
          {scene.slug_line || `场景 ${scene.scene_number}`}
        </div>
        <div className="mt-1 text-xs text-gray-500">
          节拍 {beats?.length || 0} · 镜头 {shots?.length || 0}
        </div>
      </div>
    </div>
  );
}
