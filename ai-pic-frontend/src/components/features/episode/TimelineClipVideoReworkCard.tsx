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
  storyboardAvailable,
  startEndReferenceAvailable,
  manualReferenceAvailable,
  episodeCharacters,
  selectedCharacterVirtualIpIds,
  selectedCharacterReferenceUrls,
  selectedEnvironmentReferenceUrls,
  humanReviewRequired,
  operatorReviewed,
  videoModels,
  videoModelsLoading,
  submitting,
  submitError,
  canSubmit,
  disabledReason,
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
  onOperatorReviewedChange,
}: {
  action: TimelineClipVideoReworkAction;
  prompt: string;
  model: string;
  duration: string;
  resolution: string;
  ratio: string;
  reason: string;
  videoReferenceChoice: TimelineVideoReferenceChoice;
  storyboardAvailable: boolean;
  startEndReferenceAvailable: boolean;
  manualReferenceAvailable: boolean;
  episodeCharacters: EpisodeCharacter[];
  selectedCharacterVirtualIpIds: number[];
  selectedCharacterReferenceUrls: string[];
  selectedEnvironmentReferenceUrls: string[];
  humanReviewRequired: boolean;
  operatorReviewed: boolean;
  videoModels?: VideoModelOption[];
  videoModelsLoading?: boolean;
  submitting: boolean;
  submitError: string | null;
  canSubmit: boolean;
  disabledReason?: string | null;
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
  onOperatorReviewedChange: (value: boolean) => void;
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
        className="inline-flex w-full min-w-0 items-center gap-0"
      >
        <button
          type="submit"
          aria-label="生成/重做此片段视频"
          title={disabledReason || "生成/重做此片段视频"}
          disabled={!canSubmit}
          className={operatorButtonClass(
            "primary",
            "!h-8 min-w-0 flex-1 gap-1.5 whitespace-nowrap rounded-l-md rounded-r-none border border-blue-600 px-3 shadow-none",
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
      <details
        data-clip-reference-controls="video"
        className="group mt-2 min-w-0 overflow-hidden rounded-md border border-blue-100 bg-white"
      >
        <summary className="flex cursor-pointer list-none items-center gap-2 px-2.5 py-2 text-[11px] marker:hidden [&::-webkit-details-marker]:hidden">
          <span className="font-semibold text-slate-700">视频绑定与参考</span>
          <span className="min-w-0 flex-1 truncate text-slate-500">
            IP 图 {selectedCharacterReferenceUrls.length} · 环境图{" "}
            {selectedEnvironmentReferenceUrls.length}
          </span>
          <span className="text-slate-400 transition group-open:rotate-180">
            ▾
          </span>
        </summary>
        <div className="grid gap-2 border-t border-blue-100 p-2">
          <TimelineClipVideoBindingSummary
            episodeCharacters={episodeCharacters}
            selectedCharacterVirtualIpIds={selectedCharacterVirtualIpIds}
            selectedCharacterReferenceUrls={selectedCharacterReferenceUrls}
            selectedEnvironmentReferenceUrls={selectedEnvironmentReferenceUrls}
          />
          <VideoReferenceSelect
            value={videoReferenceChoice}
            storyboardAvailable={storyboardAvailable}
            startEndAvailable={startEndReferenceAvailable}
            manualRefsAvailable={manualReferenceAvailable}
            onChange={onVideoReferenceChoiceChange}
          />
          {humanReviewRequired ? (
            <label className="flex items-start gap-2 rounded-md border border-amber-100 bg-amber-50 px-2 py-1.5 text-xs text-amber-800">
              <input
                type="checkbox"
                aria-label="已完成人工复核"
                checked={operatorReviewed}
                onChange={(event) =>
                  onOperatorReviewedChange(event.target.checked)
                }
                className="mt-0.5"
              />
              <span className="grid gap-0.5">
                <span className="font-semibold">已完成人工复核</span>
                <span>确认脚本质量、合规风险和关键帧一致性后再生视频。</span>
              </span>
            </label>
          ) : null}
        </div>
      </details>
      <div className="grid gap-2">
        {!canSubmit && disabledReason ? (
          <div
            data-clip-video-generation-gate="blocked"
            className="rounded-md bg-amber-50 px-2 py-1.5 text-xs text-amber-700"
          >
            {disabledReason}
          </div>
        ) : null}
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
