"use client";

import { operatorButtonClass } from "@/components/shared";
import type {
  EpisodeCharacter,
  TimelineClipVideoReworkAction,
} from "@/utils/api/types";
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

const CARD_CLASS = "rounded-md border border-gray-200 bg-white p-3";
const CARD_TITLE_CLASS = "text-xs font-semibold text-gray-900";
const CARD_DESCRIPTION_CLASS = "text-[11px] leading-4 text-gray-500";

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
    <section className={CARD_CLASS}>
      <div className="mb-3">
        <div className={CARD_TITLE_CLASS}>片段视频</div>
        <div className={CARD_DESCRIPTION_CLASS}>
          基于提示词、参数和可选分镜参考生成当前片段视频。
        </div>
      </div>
      <div className="grid gap-2">
        <TimelineClipVideoBindingSummary
          episodeCharacters={episodeCharacters}
          selectedCharacterVirtualIpIds={selectedCharacterVirtualIpIds}
          selectedCharacterReferenceUrls={selectedCharacterReferenceUrls}
          selectedEnvironmentReferenceUrls={selectedEnvironmentReferenceUrls}
        />
        <VideoReferenceSelect
          value={videoReferenceChoice}
          storyboardPanelIndex={storyboardPanelIndex}
          onChange={onVideoReferenceChoiceChange}
        />
        <VideoActionSelect value={action} onChange={onActionChange} />
        <label className={VIDEO_LABEL_CLASS}>
          <span>生成提示词</span>
          <textarea
            value={prompt}
            onChange={(event) => onPromptChange(event.target.value)}
            placeholder="留空则使用分镜规划的视频提示词"
            rows={3}
            className={`resize-none ${VIDEO_FIELD_CLASS}`}
          />
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
        {submitError ? (
          <div className="text-xs text-red-600">{submitError}</div>
        ) : null}
        <button
          type="submit"
          disabled={!canSubmit}
          className={operatorButtonClass("primary", "w-full")}
        >
          {submitting ? "提交中..." : "生成/重做此片段视频"}
        </button>
        <TimelineClipTaskStatusLine
          kind="video"
          task={videoTask}
          currentClipId={currentClipId ?? null}
        />
      </div>
    </section>
  );
}
