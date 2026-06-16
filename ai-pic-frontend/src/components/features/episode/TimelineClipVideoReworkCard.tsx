"use client";

import { operatorButtonClass } from "@/components/shared";
import type {
  EpisodeCharacter,
  TimelineClipVideoReworkAction,
} from "@/utils/api/types";
import { ClipProductionActionIcon } from "./ClipProductionActionIcon";
import { ClipProductionActionShell } from "./ClipProductionActionShell";
import { CompactProductionDetails } from "./CompactProductionDetails";
import { VideoReferenceSelect } from "./TimelineClipProviderReworkCardSections";
import type { TimelineVideoReferenceChoice } from "./TimelineClipProviderReworkModel";
import { TimelineClipVideoBindingSummary } from "./TimelineClipVideoBindingSummary";
import { TimelineClipTaskStatusLine } from "./TimelineClipTaskStatusLine";
import type { TrackedClipGenerationTask } from "./useTimelineClipGenerationTaskTracker";
import type { VideoModelOption } from "./TimelineClipProviderReworkControlsTypes";
import {
  VIDEO_FIELD_CLASS,
  VIDEO_FIELD_GRID_CLASS,
  VIDEO_LABEL_CLASS,
  VideoActionSelect,
  VideoModelSelect,
  VideoRatioSelect,
  VideoResolutionSelect,
} from "./TimelineClipVideoReworkFields";

export function TimelineClipVideoReworkCard({
  action,
  prompt,
  model,
  duration,
  resolution,
  ratio,
  reason,
  videoReferenceChoice,
  storyboardPanelIndex,
  startEndReferenceAvailable,
  manualReferenceAvailable,
  episodeCharacters,
  selectedCharacterVirtualIpIds,
  selectedCharacterReferenceUrls,
  selectedEnvironmentReferenceUrls,
  videoModels,
  videoModelsLoading,
  submitting,
  submitError,
  canSubmit,
  videoTask,
  currentClipId,
  onActionChange,
  onPromptChange,
  onModelChange,
  onDurationChange,
  onResolutionChange,
  onRatioChange,
  onReasonChange,
  onVideoReferenceChoiceChange,
}: {
  action: TimelineClipVideoReworkAction;
  prompt: string;
  model: string;
  duration: string;
  resolution: string;
  ratio: string;
  reason: string;
  videoReferenceChoice: TimelineVideoReferenceChoice;
  storyboardPanelIndex?: number | null;
  startEndReferenceAvailable: boolean;
  manualReferenceAvailable: boolean;
  episodeCharacters: EpisodeCharacter[];
  selectedCharacterVirtualIpIds: number[];
  selectedCharacterReferenceUrls: string[];
  selectedEnvironmentReferenceUrls: string[];
  videoModels?: VideoModelOption[];
  videoModelsLoading?: boolean;
  submitting: boolean;
  submitError: string | null;
  canSubmit: boolean;
  videoTask?: TrackedClipGenerationTask;
  currentClipId?: string | null;
  onActionChange: (value: TimelineClipVideoReworkAction) => void;
  onPromptChange: (value: string) => void;
  onModelChange: (value: string) => void;
  onDurationChange: (value: string) => void;
  onResolutionChange: (value: string) => void;
  onRatioChange: (value: string) => void;
  onReasonChange: (value: string) => void;
  onVideoReferenceChoiceChange: (value: TimelineVideoReferenceChoice) => void;
}) {
  return (
    <ClipProductionActionShell
      kind="video"
      step="3"
      title="片段视频"
      tone="primary"
    >
      <div
        data-clip-action-group="video"
        className="inline-flex w-full min-w-0 items-center gap-0 min-[720px]:w-auto"
      >
        <button
          type="submit"
          aria-label="生成/重做此片段视频"
          title="生成/重做此片段视频"
          disabled={!canSubmit}
          className={operatorButtonClass(
            "primary",
            "!h-8 min-w-0 flex-1 gap-1.5 whitespace-nowrap rounded-l-md rounded-r-none border border-blue-600 px-3 shadow-none min-[720px]:min-w-[15rem] min-[720px]:max-w-[17rem]",
          )}
        >
          <ClipProductionActionIcon kind="video" />
          <span>{submitting ? "提交中..." : "生成/重做此片段视频"}</span>
        </button>
        <CompactProductionDetails
          label="..."
          ariaLabel="展开视频绑定与参数"
          tone="primary"
          attached
        >
          <div className="grid gap-2">
            <VideoActionSelect value={action} onChange={onActionChange} />
            <label className={VIDEO_LABEL_CLASS}>
              <span>运动提示词覆盖</span>
              <textarea
                aria-label="运动提示词覆盖"
                value={prompt}
                onChange={(event) => onPromptChange(event.target.value)}
                placeholder="留空则使用 Timeline 镜头运动规划"
                rows={3}
                className={`resize-none ${VIDEO_FIELD_CLASS}`}
              />
              <span className="text-[11px] text-slate-400">
                留空则使用 Timeline 镜头运动规划
              </span>
            </label>
            <div className={VIDEO_FIELD_GRID_CLASS}>
              <VideoModelSelect
                value={model}
                videoModels={videoModels}
                videoModelsLoading={videoModelsLoading}
                onChange={onModelChange}
              />
              <label className={VIDEO_LABEL_CLASS}>
                <span>时长（秒）</span>
                <input
                  type="number"
                  min={0.1}
                  step={0.1}
                  value={duration}
                  onChange={(event) => onDurationChange(event.target.value)}
                  placeholder="默认用片段时长"
                  className={VIDEO_FIELD_CLASS}
                />
              </label>
            </div>
            <div className={VIDEO_FIELD_GRID_CLASS}>
              <VideoResolutionSelect
                value={resolution}
                onChange={onResolutionChange}
              />
              <VideoRatioSelect value={ratio} onChange={onRatioChange} />
            </div>
            <label className={VIDEO_LABEL_CLASS}>
              <span>重做原因</span>
              <input
                type="text"
                value={reason}
                onChange={(event) => onReasonChange(event.target.value)}
                placeholder="可选，会记录到该片段的资产履历"
                className={VIDEO_FIELD_CLASS}
              />
            </label>
          </div>
        </CompactProductionDetails>
      </div>
      <div
        data-clip-reference-controls="video"
        className="mt-2 grid min-w-0 gap-2 rounded-md border border-blue-100 bg-white p-2"
      >
        <TimelineClipVideoBindingSummary
          episodeCharacters={episodeCharacters}
          selectedCharacterVirtualIpIds={selectedCharacterVirtualIpIds}
          selectedCharacterReferenceUrls={selectedCharacterReferenceUrls}
          selectedEnvironmentReferenceUrls={selectedEnvironmentReferenceUrls}
        />
        <VideoReferenceSelect
          value={videoReferenceChoice}
          storyboardPanelIndex={storyboardPanelIndex}
          startEndAvailable={startEndReferenceAvailable}
          manualRefsAvailable={manualReferenceAvailable}
          onChange={onVideoReferenceChoiceChange}
        />
      </div>
      <div className="grid gap-2">
        {submitError ? (
          <div className="text-xs text-red-600">{submitError}</div>
        ) : null}
        <TimelineClipTaskStatusLine
          kind="video"
          task={videoTask}
          currentClipId={currentClipId ?? null}
        />
      </div>
    </ClipProductionActionShell>
  );
}
