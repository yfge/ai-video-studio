"use client";

import type { SceneGridInfo } from "@/utils/api/endpoints";
import type { SceneGridCharacterOption } from "./useWorkspaceSceneGridGeneration";

export function SceneGridCharacterPicker({
  characters,
  selectedIpIds,
  onToggle,
}: {
  characters: SceneGridCharacterOption[];
  selectedIpIds: number[];
  onToggle: (virtualIpId: number, checked: boolean) => void;
}) {
  if (!characters.length) return null;
  return (
    <div className="mt-3">
      <div className="text-xs text-gray-500">
        人物参考（不选则按场景绑定自动带入）
      </div>
      <div className="mt-1 flex flex-wrap gap-2">
        {characters.map((character) => {
          const ipId = character.virtual_ip_id;
          const checked = selectedIpIds.includes(ipId);
          const label = character.label;
          return (
            <label
              key={character.key}
              className={`cursor-pointer rounded-full border px-3 py-1 text-xs ${
                checked
                  ? "border-gray-900 bg-gray-900 text-white"
                  : "border-gray-300 text-gray-700"
              }`}
            >
              <input
                type="checkbox"
                className="hidden"
                checked={checked}
                onChange={(event) => onToggle(ipId, event.target.checked)}
              />
              {label}
            </label>
          );
        })}
      </div>
    </div>
  );
}

export function SceneGridResult({
  grid,
  sceneNumber,
}: {
  grid: SceneGridInfo;
  sceneNumber: number | null;
}) {
  if (!grid.image_url) return null;
  return (
    <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
      <div>
        <div className="mb-1 text-xs text-gray-500">
          宫格分镜图（{grid.rows}×{grid.columns}，
          {grid.prompt_source === "llm_dynamic"
            ? "LLM 动态提示词"
            : "模板提示词"}
          ）
        </div>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={grid.image_url}
          alt={`场景${sceneNumber}宫格分镜图`}
          className="w-full rounded-md border border-gray-200"
        />
      </div>
      <div className="space-y-3">
        {grid.video_url ? (
          <div>
            <div className="mb-1 text-xs text-gray-500">
              连续成片（{grid.video_model || "Seedance"}）
            </div>
            <video
              className="w-full rounded-md border border-gray-200"
              controls
              preload="none"
              poster={grid.video_thumbnail_url || undefined}
              src={grid.video_url}
            />
          </div>
        ) : (
          <div className="rounded-md border border-dashed border-gray-300 p-3 text-xs text-gray-500">
            尚未生成成片，点击上方“宫格图生成成片”。
          </div>
        )}
        {grid.cells?.length ? (
          <div className="max-h-48 overflow-auto rounded-md border border-gray-200 p-2 text-xs text-gray-600">
            {grid.cells.map((cell) => (
              <div key={cell.panel_index}>
                {String(cell.panel_index).padStart(2, "0")}｜
                {cell.title || cell.caption}
                {cell.duration ? `（约${cell.duration}s）` : ""}
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
