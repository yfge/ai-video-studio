"use client";

import { operatorButtonClass, operatorSelectClass } from "@/components/shared";
import type {
  EpisodeCharacter,
  TimelineClipVideoReworkAction,
} from "@/utils/api/types";
import { VideoReferenceSelect } from "./TimelineClipProviderReworkCardSections";
import type { TimelineVideoReferenceChoice } from "./TimelineClipProviderReworkModel";
import { TimelineClipVideoBindingSummary } from "./TimelineClipVideoBindingSummary";
import { TimelineClipTaskStatusLine } from "./TimelineClipTaskStatusLine";
import type { TrackedClipGenerationTask } from "./useTimelineClipGenerationTaskTracker";

const VIDEO_ACTION_OPTIONS: Array<{
  value: TimelineClipVideoReworkAction;
  label: string;
}> = [
  { value: "re_cut", label: "重新切分" },
  { value: "re_render", label: "重新渲染" },
];

const RESOLUTION_OPTIONS = ["720p", "1080p"];
const FIELD_CLASS = [
  "rounded-md border border-gray-200 px-2 py-1.5 text-xs",
  "outline-none focus:border-gray-400",
].join(" ");
const FIELD_GRID_CLASS = "grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)] gap-2";
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
          基于提示词、参数和可选故事板参考生成当前片段视频。
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
        <textarea
          value={prompt}
          onChange={(event) => onPromptChange(event.target.value)}
          placeholder="生成提示词"
          rows={3}
          className={`resize-none ${FIELD_CLASS}`}
        />
        <div className={FIELD_GRID_CLASS}>
          <input
            type="text"
            value={model}
            onChange={(event) => onModelChange(event.target.value)}
            placeholder="model"
            className={FIELD_CLASS}
          />
          <input
            type="number"
            min={0.1}
            step={0.1}
            value={duration}
            onChange={(event) => onDurationChange(event.target.value)}
            placeholder="秒"
            className={FIELD_CLASS}
          />
        </div>
        <div className={FIELD_GRID_CLASS}>
          <ResolutionSelect value={resolution} onChange={onResolutionChange} />
          <input
            type="text"
            value={ratio}
            onChange={(event) => onRatioChange(event.target.value)}
            placeholder="ratio"
            className={FIELD_CLASS}
          />
        </div>
        <input
          type="text"
          value={reason}
          onChange={(event) => onReasonChange(event.target.value)}
          placeholder="原因"
          className={FIELD_CLASS}
        />
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

function VideoActionSelect({
  value,
  onChange,
}: {
  value: TimelineClipVideoReworkAction;
  onChange: (value: TimelineClipVideoReworkAction) => void;
}) {
  return (
    <select
      value={value}
      onChange={(event) =>
        onChange(event.target.value as TimelineClipVideoReworkAction)
      }
      className={operatorSelectClass("w-full")}
    >
      {VIDEO_ACTION_OPTIONS.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

function ResolutionSelect({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className={operatorSelectClass("w-full")}
    >
      {RESOLUTION_OPTIONS.map((option) => (
        <option key={option} value={option}>
          {option}
        </option>
      ))}
    </select>
  );
}
