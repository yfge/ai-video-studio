"use client";

import { useEffect, useMemo, useState } from "react";
import type { NormalizedScene, Script } from "@/utils/api/types";
import { Timeline } from "@/components/features";
import {
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
  StatusPill,
  operatorButtonClass,
  operatorSelectClass,
} from "@/components/shared";
import { getString } from "@/hooks/useEpisodeDetail";
import { useAvailableModels } from "@/hooks/useAvailableModels";
import {
  firstTimelineItemId,
  resolveTimelineSelection,
} from "@/components/features/Timeline/timelineViewModel";
import {
  buildEpisodeTimelineTracks,
  formatTimelineMs,
  timelineItemMeta,
} from "./EpisodeTimelineWorkspaceModel";
import { ContextRow, InspectorRow } from "./EpisodeTimelineWorkspaceParts";

interface EpisodeTimelineWorkspaceProps {
  selectedScriptId: number | null;
  selectedScript: Script | null;
  selectedAudioTimeline: Record<string, unknown> | null;
  selectedStoryboard: Record<string, unknown> | null;
  normalizedScenes: NormalizedScene[];
  normalizedScenesLoading: boolean;
  normalizedScenesError: string | null;
  pipelineBusy?: boolean;
  timingModel: string;
  setTimingModel: (value: string) => void;
  useDurationControl: boolean;
  setUseDurationControl: (value: boolean) => void;
  onGenerateTimelinePipeline?: () => void;
  pipelineTaskId?: number | null;
  onNavigateToTasks: () => void;
  onNavigateToScript: () => void;
}

export function EpisodeTimelineWorkspace(props: EpisodeTimelineWorkspaceProps) {
  const {
    selectedScriptId,
    selectedScript,
    selectedAudioTimeline,
    selectedStoryboard,
    normalizedScenes,
    normalizedScenesLoading,
    normalizedScenesError,
    pipelineBusy,
    timingModel,
    setTimingModel,
    useDurationControl,
    setUseDurationControl,
    onGenerateTimelinePipeline,
    pipelineTaskId,
    onNavigateToTasks,
    onNavigateToScript,
  } = props;
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const { models, loading: modelsLoading } = useAvailableModels({
    modelType: "text",
    enabled: true,
  });

  const tracks = useMemo(
    () => buildEpisodeTimelineTracks(selectedAudioTimeline, selectedStoryboard),
    [selectedAudioTimeline, selectedStoryboard],
  );
  const selection = resolveTimelineSelection(tracks, selectedItemId);
  const meta = timelineItemMeta(selection.item);

  useEffect(() => {
    if (!selection.item) setSelectedItemId(firstTimelineItemId(tracks));
  }, [selection.item, tracks]);

  return (
    <div className="grid gap-4 xl:grid-cols-[260px_minmax(0,1fr)_320px]">
      <OperatorPanel className="p-4">
        <h2 className="text-sm font-semibold">剧集上下文</h2>
        <div className="mt-4 space-y-3 text-xs text-gray-600">
          <ContextRow label="剧本版本" value={selectedScript?.version || "未选择"} />
          <ContextRow label="场景数量" value={String(normalizedScenes.length)} />
          <ContextRow
            label="时间轴"
            value={selectedAudioTimeline ? "已生成" : "未生成"}
            ready={Boolean(selectedAudioTimeline)}
          />
          <ContextRow
            label="分镜占位"
            value={selectedStoryboard ? "已生成" : "未生成"}
            ready={Boolean(selectedStoryboard)}
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
      </OperatorPanel>

      <OperatorPanel>
        <OperatorSectionHeader
          title="时间轴主画布"
          subtitle="对白音轨、时间轴、分镜占位按同一时间码对齐"
          action={
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={timingModel}
                onChange={(event) => setTimingModel(event.target.value)}
                disabled={modelsLoading}
                className={operatorSelectClass("w-40")}
              >
                <option value="">自动模型</option>
                {models.map((model) => {
                  const value = model.model_id || `${model.provider}:${model.id}`;
                  return (
                    <option key={value} value={value}>
                      {model.name || model.id}
                    </option>
                  );
                })}
              </select>
              <label className="flex items-center gap-1 text-xs text-gray-600">
                <input
                  type="checkbox"
                  checked={useDurationControl}
                  onChange={(event) => setUseDurationControl(event.target.checked)}
                />
                时长精控
              </label>
              <button
                type="button"
                onClick={onGenerateTimelinePipeline}
                disabled={pipelineBusy || !selectedScriptId}
                className={operatorButtonClass("primary")}
              >
                {pipelineBusy ? "生成中..." : "生成时间轴"}
              </button>
            </div>
          }
        />
        <div className="p-4">
          {tracks.length ? (
            <Timeline
              tracks={tracks}
              selectedItemId={selectedItemId}
              onSelect={(item) => setSelectedItemId(item.id)}
              initialZoom={1}
            />
          ) : (
            <OperatorState title="选择剧本并生成时间轴后，这里会显示对白和分镜轨道。" />
          )}
        </div>
        {pipelineTaskId ? (
          <div className="border-t border-gray-100 px-4 py-3 text-xs text-blue-700">
            一键流水线任务已创建：task_id={pipelineTaskId}
          </div>
        ) : null}
      </OperatorPanel>

      <OperatorPanel className="p-4">
        <h2 className="text-sm font-semibold">片段检查器</h2>
        {selection.item ? (
          <div className="mt-4 space-y-4">
            <StatusPill tone={selection.track?.id === "storyboard" ? "blue" : "green"}>
              {selection.track?.label || "片段"}
            </StatusPill>
            <InspectorRow label="内容" value={selection.item.label || "未命名"} />
            <InspectorRow
              label="时间"
              value={`${formatTimelineMs(selection.item.startMs)} - ${formatTimelineMs(
                selection.item.endMs,
              )}`}
            />
            <InspectorRow label="角色" value={getString(meta.character) || "—"} />
            <InspectorRow
              label="镜头"
              value={getString(meta.shot_type) || getString(meta.camera_notes) || "—"}
            />
            <InspectorRow label="状态" value={getString(meta.status) || "待复核"} />
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
          </div>
        ) : (
          <div className="mt-4 text-sm text-gray-500">请选择时间轴片段。</div>
        )}
        <div className="mt-5 flex gap-2 border-t border-gray-100 pt-4">
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
      </OperatorPanel>
    </div>
  );
}
