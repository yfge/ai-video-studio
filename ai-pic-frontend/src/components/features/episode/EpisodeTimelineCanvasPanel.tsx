"use client";

import { useState, type Ref } from "react";
import {
  Timeline,
  type TimelineItem,
  type TimelineTrack,
} from "@/components/features";
import { operatorButtonClass, operatorSelectClass } from "@/components/shared";
import { GenerationTaskStatusLine } from "@/components/shared/notifications";

type ModelOption = {
  id?: string;
  provider?: string | null;
  model_id?: string | null;
  name?: string | null;
};

export function EpisodeTimelineCanvasPanel({
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
}) {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const hasVideoItems = tracks.some(
    (track) =>
      track.id === "video" || track.items.some((item) => item.type === "video"),
  );
  const showSettings = settingsOpen || tracks.length === 0 || !hasVideoItems;
  const timelineTracks = tracks.length ? tracks : EMPTY_TIMELINE_TRACKS;

  return (
    <section
      id="episode-timeline-canvas"
      ref={timelineCanvasRef}
      data-timeline-canvas-panel="primary"
      data-timeline-canvas-presence-frame="restored-visible-axis"
      data-timeline-selection-visibility="anchor"
      aria-label="Timeline 全片时间轴定位区"
      className="scroll-mt-16 space-y-2 rounded-xl bg-blue-50/35 p-1 shadow-[inset_0_0_0_1px_rgba(191,219,254,0.9)]"
    >
      <div className="space-y-2">
        {showSettings ? (
          <TimelineGenerationSettings
            selectedScriptId={selectedScriptId}
            timingModel={timingModel}
            setTimingModel={setTimingModel}
            models={models}
            modelsLoading={modelsLoading}
            useDurationControl={useDurationControl}
            setUseDurationControl={setUseDurationControl}
            pipelineBusy={pipelineBusy}
            onGenerateTimelinePipeline={onGenerateTimelinePipeline}
          />
        ) : null}
        <Timeline
          tracks={timelineTracks}
          selectedItemId={tracks.length ? selectedItemId : null}
          onSelect={tracks.length ? onSelectItem : undefined}
          startMs={tracks.length ? undefined : 0}
          endMs={tracks.length ? undefined : 10000}
          initialZoom={1}
          fitToWidth={true}
          headerTitle="全片时间轴"
          headerAction={
            <button
              type="button"
              onClick={() => setSettingsOpen((value) => !value)}
              aria-label="Timeline 生成设置"
              title="Timeline 生成设置"
              className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-transparent bg-transparent text-slate-600 transition-colors hover:bg-white/80 hover:text-slate-950 disabled:pointer-events-none disabled:opacity-50"
            >
              <TimelineSettingsIcon active={showSettings} />
            </button>
          }
        />
      </div>
      {pipelineTask ? (
        <div className="rounded-md border border-gray-100 bg-white px-3 py-1.5">
          <GenerationTaskStatusLine label="时间轴流水线" task={pipelineTask} />
        </div>
      ) : null}
    </section>
  );
}

const EMPTY_TIMELINE_TRACKS: TimelineTrack[] = [
  { id: "video", label: "视频", color: "#0f766e", items: [] },
];

function TimelineSettingsIcon({ active }: { active: boolean }) {
  return (
    <svg
      aria-hidden="true"
      data-timeline-settings-icon="pipeline"
      className="h-3.5 w-3.5"
      fill="none"
      stroke="currentColor"
      strokeLinejoin="round"
      strokeLinecap="round"
      strokeWidth={active ? "2" : "1.7"}
      viewBox="0 0 16 16"
    >
      <circle cx="4" cy="4" r="1.4" fill="white" />
      <circle cx="12" cy="4" r="1.4" fill="white" />
      <circle cx="8" cy="12" r="1.4" fill="white" />
      <path d="M5.2 4h5.6" />
      <path d="M4.8 5.1 7.2 10.8" />
      <path d="M11.2 5.1 8.8 10.8" />
    </svg>
  );
}

function TimelineGenerationSettings({
  selectedScriptId,
  timingModel,
  setTimingModel,
  models,
  modelsLoading,
  useDurationControl,
  setUseDurationControl,
  pipelineBusy,
  onGenerateTimelinePipeline,
}: {
  selectedScriptId: number | null;
  timingModel: string;
  setTimingModel: (value: string) => void;
  models: ModelOption[];
  modelsLoading: boolean;
  useDurationControl: boolean;
  setUseDurationControl: (value: boolean) => void;
  pipelineBusy?: boolean;
  onGenerateTimelinePipeline?: () => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-md border border-gray-100 bg-gray-50 px-3 py-2">
      <span className="text-xs font-semibold text-gray-600">
        Timeline 生成设置
      </span>
      <select
        value={timingModel}
        onChange={(event) => setTimingModel(event.target.value)}
        disabled={modelsLoading}
        className={operatorSelectClass("w-48")}
      >
        <option value="">自动模型</option>
        {models.map((model) => {
          const providerScopedId =
            model.provider && model.id
              ? `${model.provider}:${model.id}`
              : model.id;
          const value = model.model_id || providerScopedId || model.name || "";
          if (!value) return null;
          return (
            <option key={value} value={value}>
              {model.name || model.model_id || model.id}
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
        {pipelineBusy ? "生成中..." : "生成 Timeline"}
      </button>
    </div>
  );
}
