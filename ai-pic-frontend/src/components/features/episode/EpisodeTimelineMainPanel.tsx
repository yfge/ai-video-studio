"use client";

import type { ReactNode, Ref } from "react";
import type { TimelineItem, TimelineTrack } from "@/components/features";
import { OperatorMainCanvas } from "@/components/shared";
import type {
  TimelineRenderJobResponse,
  TimelineRenderType,
} from "@/utils/api/types";
import type { TimelineRenderReadiness } from "./EpisodeTimelineRenderModel";
import { EpisodeTimelineCanvasPanel } from "./EpisodeTimelineCanvasPanel";
import { TimelineRenderPanel } from "./EpisodeTimelineRenderPanel";

type ModelOption = {
  id?: string;
  provider?: string | null;
  model_id?: string | null;
  name?: string | null;
};

export function EpisodeTimelineMainPanel({
  tracks,
  selectedItemId,
  timelineCanvasRef,
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
  pipelineTask,
  renderReadiness,
  latestRenderJob,
  renderJobsLoading,
  renderBusy,
  renderError,
  clipProductionPanel,
  onQueueRender,
  onRetryRender,
}: {
  tracks: TimelineTrack[];
  selectedItemId: string | null;
  timelineCanvasRef?: Ref<HTMLElement>;
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
  pipelineTask?: {
    taskId: number;
    phase: string;
    error: string | null;
  } | null;
  renderReadiness: TimelineRenderReadiness;
  latestRenderJob: TimelineRenderJobResponse | null;
  renderJobsLoading: boolean;
  renderBusy: boolean;
  renderError: string | null;
  clipProductionPanel?: ReactNode;
  onQueueRender: (renderType: TimelineRenderType) => void;
  onRetryRender: (renderType: TimelineRenderType) => void;
}) {
  return (
    <OperatorMainCanvas>
      <div
        data-episode-timeline-main-layout="timeline-and-assets"
        className="space-y-3 bg-slate-100/70 p-2 min-[760px]:p-3"
      >
        <EpisodeTimelineCanvasPanel
          tracks={tracks}
          selectedItemId={selectedItemId}
          timelineCanvasRef={timelineCanvasRef}
          onSelectItem={onSelectItem}
          selectedScriptId={selectedScriptId}
          timingModel={timingModel}
          setTimingModel={setTimingModel}
          models={models}
          modelsLoading={modelsLoading}
          useDurationControl={useDurationControl}
          setUseDurationControl={setUseDurationControl}
          pipelineBusy={pipelineBusy}
          onGenerateTimelinePipeline={onGenerateTimelinePipeline}
          pipelineTask={pipelineTask}
        />
        {clipProductionPanel}
        <section
          data-episode-render-strip="compact"
          data-episode-render-strip-surface="episode-output-asset"
          data-episode-render-strip-style="asset-footer"
          className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-[0_8px_24px_rgba(15,23,42,0.05)]"
        >
          <TimelineRenderPanel
            readiness={renderReadiness}
            latestJob={latestRenderJob}
            loading={renderJobsLoading}
            busy={renderBusy}
            error={renderError}
            onQueueRender={onQueueRender}
            onRetryRender={onRetryRender}
          />
        </section>
      </div>
    </OperatorMainCanvas>
  );
}
