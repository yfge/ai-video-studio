"use client";

import {
  OperatorContextRail,
  StatusPill,
  operatorButtonClass,
  operatorSelectClass,
} from "@/components/shared";
import { getString } from "@/hooks/useEpisodeDetail";
import type { Environment, NormalizedScene } from "@/utils/api/types";
import type { TimelineItem, TimelineTrack } from "@/components/features";
import { formatTimelineMs, timelineItemMeta } from "./EpisodeTimelineWorkspaceModel";

export function ContextRow({
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
      <span className={ready ? "text-green-700" : "text-gray-500"}>{value}</span>
    </div>
  );
}

export function InspectorRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="text-sm">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="mt-1 text-gray-900">{value}</div>
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
        <ContextRow label="剧本版本" value={selectedScriptVersion || "未选择"} />
        <ContextRow label="场景数量" value={String(normalizedScenes.length)} />
        <ContextRow label="时间轴" value={timelineReady ? "已生成" : "未生成"} ready={timelineReady} />
        <ContextRow label="分镜占位" value={storyboardReady ? "已生成" : "未生成"} ready={storyboardReady} />
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

export function EpisodeTimelineInspectorContent({
  item,
  track,
  scene,
  environments,
  selectedEnvironmentId,
  environmentSaving,
  onEnvironmentChange,
  onSaveEnvironment,
  onNavigateToScript,
  onNavigateToTasks,
}: {
  item: TimelineItem | null;
  track: TimelineTrack | null;
  scene: NormalizedScene | null;
  environments: Environment[];
  selectedEnvironmentId: number | null;
  environmentSaving: boolean;
  onEnvironmentChange: (value: number | null) => void;
  onSaveEnvironment: () => void;
  onNavigateToScript: () => void;
  onNavigateToTasks: () => void;
}) {
  if (!item) {
    return <div className="mt-4 text-sm text-gray-500">请选择时间轴片段。</div>;
  }

  const meta = timelineItemMeta(item);
  return (
    <div className="mt-4 space-y-4">
      <StatusPill tone={track?.id === "storyboard" ? "blue" : "green"}>
        {track?.label || "片段"}
      </StatusPill>
      <InspectorRow label="内容" value={item.label || "未命名"} />
      <InspectorRow
        label="时间"
        value={`${formatTimelineMs(item.startMs)} - ${formatTimelineMs(item.endMs)}`}
      />
      <InspectorRow label="角色" value={getString(meta.character) || "—"} />
      <InspectorRow
        label="镜头"
        value={getString(meta.shot_type) || getString(meta.camera_notes) || "—"}
      />
      <InspectorRow label="状态" value={getString(meta.status) || "待复核"} />

      <section className="rounded-md border border-gray-200 p-3">
        <div className="text-sm font-semibold text-gray-950">场景环境</div>
        {scene ? (
          <div className="mt-3 space-y-2">
            <div className="text-xs text-gray-500">
              场景 {scene.scene_number} · {scene.slug_line}
            </div>
            <select
              value={selectedEnvironmentId ?? ""}
              onChange={(event) =>
                onEnvironmentChange(
                  event.target.value ? Number(event.target.value) : null,
                )
              }
              className={operatorSelectClass("w-full")}
            >
              <option value="" disabled>
                选择场景环境
              </option>
              {environments.map((env) => (
                <option key={env.id} value={env.id}>
                  {env.name}
                  {(env.linked_virtual_ip_count || 0) > 0 ? " · IP资产" : ""}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={onSaveEnvironment}
              disabled={environmentSaving || selectedEnvironmentId === null}
              className={operatorButtonClass("primary", "w-full")}
            >
              {environmentSaving ? "保存中..." : "保存场景环境"}
            </button>
          </div>
        ) : (
          <div className="mt-2 text-xs text-amber-700">
            未找到对应规范化场景，请先生成剧本结构或时间轴。
          </div>
        )}
      </section>

      <div className="grid grid-cols-2 gap-2">
        <button type="button" className={operatorButtonClass("secondary")}>
          重新配音
        </button>
        <button type="button" className={operatorButtonClass("secondary")}>
          生成分镜
        </button>
        <button type="button" className={operatorButtonClass("secondary")}>
          标记问题
        </button>
        <button type="button" className={operatorButtonClass("primary")}>
          继续生成
        </button>
      </div>
      <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
        分镜生成中 48%
      </div>
      <div className="flex gap-2 border-t border-gray-100 pt-4">
        <button
          type="button"
          onClick={onNavigateToScript}
          className={operatorButtonClass("secondary")}
        >
          剧本
        </button>
        <button
          type="button"
          onClick={onNavigateToTasks}
          className={operatorButtonClass("secondary")}
        >
          任务
        </button>
      </div>
    </div>
  );
}
