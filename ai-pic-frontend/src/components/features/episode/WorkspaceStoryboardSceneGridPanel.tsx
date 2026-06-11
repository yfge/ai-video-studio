"use client";

import { OperatorPanel, OperatorSectionHeader } from "@/components/shared";
import type { NormalizedScene } from "@/utils/api/types";
import {
  SceneGridCharacterPicker,
  SceneGridResult,
} from "./WorkspaceStoryboardSceneGridParts";
import { useWorkspaceSceneGridGeneration } from "./useWorkspaceSceneGridGeneration";

type ShowAlert = (options: {
  message: string;
  variant: "info" | "success" | "warning" | "error";
}) => void;

const GRID_SIZE_OPTIONS = [6, 9, 12, 16];

export function WorkspaceStoryboardSceneGridPanel({
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
  const {
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
  } = useWorkspaceSceneGridGeneration({
    episodeKey,
    selectedScriptId,
    normalizedScenes,
    showAlert,
  });

  if (!selectedScriptId || !sceneNumbers.length) return null;

  return (
    <OperatorPanel>
      <OperatorSectionHeader
        title="场景宫格分镜"
        subtitle="按场景生成一张宫格分镜大图，再用 Seedance 参考宫格图生成连续成片"
        action={
          <button
            type="button"
            className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-800"
            onClick={() => setExpanded((prev) => !prev)}
          >
            {expanded ? "收起" : "展开"}
          </button>
        }
      />
      {!expanded ? null : (
        <>
          <div className="mt-4 flex flex-wrap items-end gap-3 text-sm">
            <label className="flex flex-col gap-1 text-xs text-gray-600">
              场景
              <select
                className="rounded-md border border-gray-300 px-2 py-1.5 text-sm"
                value={sceneNumber ?? ""}
                onChange={(event) => setSceneNumber(Number(event.target.value))}
              >
                {sceneNumbers.map((value) => (
                  <option key={value} value={value}>
                    场景 {value}
                    {grids[String(value)]?.image_url ? " ·已生成" : ""}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-xs text-gray-600">
              宫格数
              <select
                className="rounded-md border border-gray-300 px-2 py-1.5 text-sm"
                value={gridSize}
                onChange={(event) => setGridSize(Number(event.target.value))}
              >
                {GRID_SIZE_OPTIONS.map((value) => (
                  <option key={value} value={value}>
                    {value} 格
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="rounded-md bg-gray-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
              disabled={submitting || sheetActive}
              onClick={() => void handleGenerateSheet()}
            >
              {sheetActive ? "宫格图生成中…" : "生成宫格分镜图"}
            </button>
            <button
              type="button"
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-800 disabled:opacity-50"
              disabled={submitting || videoActive || !currentGrid?.image_url}
              onClick={() => void handleGenerateVideo()}
            >
              {videoActive ? "成片生成中…" : "宫格图生成成片"}
            </button>
          </div>

          <SceneGridCharacterPicker
            characters={characters}
            selectedIpIds={selectedIpIds}
            onToggle={(ipId, checked) =>
              setSelectedIpIds((prev) =>
                checked
                  ? [...prev, ipId]
                  : prev.filter((value) => value !== ipId),
              )
            }
          />

          <label className="mt-3 flex flex-col gap-1 text-xs text-gray-600">
            环境参考图 URL（可选，逗号或换行分隔；不填则按场景环境自动带入）
            <input
              className="rounded-md border border-gray-300 px-2 py-1.5 text-sm"
              placeholder="https://…"
              value={environmentUrls}
              onChange={(event) => setEnvironmentUrls(event.target.value)}
            />
          </label>

          {currentGrid ? (
            <SceneGridResult grid={currentGrid} sceneNumber={sceneNumber} />
          ) : null}
        </>
      )}
    </OperatorPanel>
  );
}
