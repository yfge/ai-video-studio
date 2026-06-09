"use client";

import type { ReactNode } from "react";
import type { TimelineItem, TimelineTrack } from "@/components/features";
import {
  StatusPill,
  operatorButtonClass,
  operatorSelectClass,
} from "@/components/shared";
import { getString } from "@/hooks/useEpisodeDetail";
import type { Environment, NormalizedScene } from "@/utils/api/types";
import {
  formatTimelineMs,
  timelineItemMeta,
} from "./EpisodeTimelineWorkspaceModel";
import { timelineClipVideoStatus } from "./EpisodeTimelineRenderModel";

export function ClipProductionSummary({
  item,
  track,
  selectedStoryboard,
}: {
  item: TimelineItem | null;
  track: TimelineTrack | null;
  selectedStoryboard: Record<string, unknown> | null;
}) {
  if (!item) {
    return <div className="text-sm text-gray-500">请选择时间轴片段。</div>;
  }
  const meta = timelineItemMeta(item);
  const videoStatus = timelineClipVideoStatus(meta, selectedStoryboard);
  return (
    <div className="grid gap-3 rounded-md border border-gray-200 bg-gray-50 p-3 md:grid-cols-5">
      <SummaryCell label="类型">
        <StatusPill tone={track?.id === "storyboard" ? "blue" : "green"}>
          {track?.label || "片段"}
        </StatusPill>
      </SummaryCell>
      <SummaryCell label="内容">{item.label || "未命名"}</SummaryCell>
      <SummaryCell label="时间">
        {formatTimelineMs(item.startMs)} - {formatTimelineMs(item.endMs)}
      </SummaryCell>
      <SummaryCell label="状态">
        {getString(meta.status) || "待复核"}
      </SummaryCell>
      <SummaryCell label="视频素材">
        {videoStatus.ready
          ? `已关联 · ${videoStatus.source || "素材"}`
          : "缺少视频素材"}
      </SummaryCell>
    </div>
  );
}

function SummaryCell({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="min-w-0 text-xs">
      <div className="text-gray-500">{label}</div>
      <div className="mt-1 truncate font-medium text-gray-950">{children}</div>
    </div>
  );
}

export function ClipEnvironmentSection({
  scene,
  environments,
  selectedEnvironmentId,
  environmentSaving,
  onEnvironmentChange,
  onSaveEnvironment,
}: {
  scene: NormalizedScene | null;
  environments: Environment[];
  selectedEnvironmentId: number | null;
  environmentSaving: boolean;
  onEnvironmentChange: (value: number | null) => void;
  onSaveEnvironment: () => void;
}) {
  return (
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
  );
}

export function ClipNavigationActions({
  videoReady,
  onNavigateToScript,
  onNavigateToStoryboard,
  onNavigateToTasks,
}: {
  videoReady: boolean;
  onNavigateToScript: () => void;
  onNavigateToStoryboard: () => void;
  onNavigateToTasks: () => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      <button
        type="button"
        onClick={onNavigateToScript}
        className={operatorButtonClass("secondary")}
      >
        剧本
      </button>
      <button
        type="button"
        onClick={onNavigateToStoryboard}
        className={operatorButtonClass(videoReady ? "secondary" : "primary")}
      >
        替换片段
      </button>
      <button
        type="button"
        onClick={onNavigateToTasks}
        className={operatorButtonClass("secondary")}
      >
        任务
      </button>
    </div>
  );
}
