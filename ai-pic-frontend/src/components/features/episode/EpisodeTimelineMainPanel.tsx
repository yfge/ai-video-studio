"use client";

import type { TimelineItem, TimelineTrack } from "@/components/features";
import { Timeline } from "@/components/features";
import {
  OperatorMainCanvas,
  OperatorPanel,
  OperatorSectionHeader,
  OperatorState,
  operatorButtonClass,
  operatorSelectClass,
} from "@/components/shared";
import type {
  TimelineRenderJobResponse,
  TimelineRenderType,
} from "@/utils/api/types";
import type { TimelineRenderReadiness } from "./EpisodeTimelineRenderModel";
import { TimelineRenderPanel } from "./EpisodeTimelineRenderPanel";

type ModelOption = {
  id: string;
  provider?: string | null;
  model_id?: string | null;
  name?: string | null;
};

export function EpisodeTimelineMainPanel({
  tracks,
  selectedItemId,
  onSelectItem,
  selectedScriptId,
  timingModel,
  setTimingModel,
  models,
  modelsLoading,
  useDurationControl,
  setUseDurationControl,
  pipelineBusy,
  onGenerateTimelinePipeline,
  pipelineTaskId,
  renderReadiness,
  latestRenderJob,
  renderJobsLoading,
  renderBusy,
  renderError,
  onQueueRender,
  onRetryRender,
}: {
  tracks: TimelineTrack[];
  selectedItemId: string | null;
  onSelectItem: (item: TimelineItem) => void;
  selectedScriptId: number | null;
  timingModel: string;
  setTimingModel: (value: string) => void;
  models: ModelOption[];
  modelsLoading: boolean;
  useDurationControl: boolean;
  setUseDurationControl: (value: boolean) => void;
  pipelineBusy?: boolean;
  onGenerateTimelinePipeline?: () => void;
  pipelineTaskId?: number | null;
  renderReadiness: TimelineRenderReadiness;
  latestRenderJob: TimelineRenderJobResponse | null;
  renderJobsLoading: boolean;
  renderBusy: boolean;
  renderError: string | null;
  onQueueRender: (renderType: TimelineRenderType) => void;
  onRetryRender: (renderType: TimelineRenderType) => void;
}) {
  return (
    <OperatorMainCanvas>
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
                  const value =
                    model.model_id || `${model.provider}:${model.id}`;
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
                  onChange={(event) =>
                    setUseDurationControl(event.target.checked)
                  }
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
              onSelect={onSelectItem}
              initialZoom={1}
            />
          ) : (
            <OperatorState title="选择剧本并生成时间轴后，这里会显示对白和分镜轨道。" />
          )}
        </div>
        <TimelineRenderPanel
          readiness={renderReadiness}
          latestJob={latestRenderJob}
          loading={renderJobsLoading}
          busy={renderBusy}
          error={renderError}
          onQueueRender={onQueueRender}
          onRetryRender={onRetryRender}
        />
        {pipelineTaskId ? (
          <div className="border-t border-gray-100 px-4 py-3 text-xs text-blue-700">
            一键流水线任务已创建：task_id={pipelineTaskId}
          </div>
        ) : null}
      </OperatorPanel>
    </OperatorMainCanvas>
  );
}
