"use client";

import { OperatorContextRail } from "@/components/shared";
import type { NormalizedScene } from "@/utils/api/types";

function ContextRow({
  label,
  value,
  ready,
}: {
  label: string;
  value: string;
  ready?: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <span>{label}</span>
      <span className={ready ? "text-green-700" : "text-gray-500"}>
        {value}
      </span>
    </div>
  );
}

export function EpisodeTimelineContextRail({
  selectedScriptVersion,
  normalizedScenes,
  normalizedScenesLoading,
  normalizedScenesError,
  timelineReady,
  storyboardReady,
}: {
  selectedScriptVersion?: string | null;
  normalizedScenes: NormalizedScene[];
  normalizedScenesLoading: boolean;
  normalizedScenesError: string | null;
  timelineReady: boolean;
  storyboardReady: boolean;
}) {
  return (
    <OperatorContextRail title="剧集上下文" subtitle="剧本、场景和生成状态">
      <div className="space-y-3 text-xs text-gray-600">
        <ContextRow
          label="剧本版本"
          value={selectedScriptVersion || "未选择"}
        />
        <ContextRow label="场景数量" value={String(normalizedScenes.length)} />
        <ContextRow
          label="时间轴"
          value={timelineReady ? "已生成" : "未生成"}
          ready={timelineReady}
        />
        <ContextRow
          label="分镜占位"
          value={storyboardReady ? "已生成" : "未生成"}
          ready={storyboardReady}
        />
      </div>
      <div className="mt-5 border-t border-gray-100 pt-4">
        <div className="mb-2 text-xs font-medium text-gray-500">场景列表</div>
        {normalizedScenesLoading ? (
          <div className="text-xs text-gray-400">加载中...</div>
        ) : normalizedScenesError ? (
          <div className="text-xs text-red-600">{normalizedScenesError}</div>
        ) : (
          <div className="space-y-1">
            {normalizedScenes.slice(0, 10).map((scene) => (
              <div
                key={scene.id}
                className="rounded border border-gray-100 px-2 py-1.5 text-xs"
              >
                <span className="font-medium">场景 {scene.scene_number}</span>
                <span className="ml-2 text-gray-500">{scene.slug_line}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </OperatorContextRail>
  );
}
