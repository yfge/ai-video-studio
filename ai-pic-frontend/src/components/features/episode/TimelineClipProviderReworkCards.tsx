"use client";

import type { FormEvent } from "react";
import type {
  EpisodeCharacter,
  TimelineClipVideoReworkAction,
} from "@/utils/api/types";
import { TimelineClipKeyframeCard } from "./TimelineClipKeyframeCard";
import { TimelineClipSharedReferenceContext } from "./TimelineClipSharedReferenceContext";
import { StoryboardReferenceCard } from "./TimelineClipStoryboardReferenceCard";
import { TimelineClipVideoReworkCard } from "./TimelineClipVideoReworkCard";
import type { TimelineVideoReferenceChoice } from "./TimelineClipProviderReworkModel";
import type { TimelineClipStoryboardReferenceSelection } from "./useTimelineClipStoryboardReferenceSelection";
import type { ClipGenerationTaskMap } from "./useTimelineClipGenerationTaskTracker";
import type { VideoModelOption } from "./TimelineClipProviderReworkControlsTypes";

const COMMAND_SURFACE_CLASS = [
  "w-full bg-transparent p-0 shadow-none",
  "min-[720px]:w-auto min-[720px]:rounded-md min-[720px]:border min-[720px]:border-slate-200 min-[720px]:bg-white min-[720px]:p-0.5 min-[720px]:shadow-[0_1px_2px_rgba(15,23,42,0.05)]",
].join(" ");
const COMMAND_GRID_CLASS = [
  "grid grid-cols-2 items-stretch gap-1",
  "min-[720px]:grid-cols-[max-content_max-content_minmax(15rem,17rem)] min-[720px]:justify-start min-[720px]:gap-0.5",
].join(" ");

export function TimelineClipProviderReworkCards({
  action,
  prompt,
  model,
  duration,
  resolution,
  ratio,
  reason,
  videoReferenceChoice,
  referenceImagesInput,
  keyframeStatus,
  manualReferenceAvailable,
  storyboardStyle,
  storyboardPanelCount,
  storyboardPanelIndex,
  storyboardSheetUrl,
  episodeCharacters,
  episodeCharactersLoading,
  episodeCharactersError,
  onNavigateToCharacters,
  selectedStoryboardVirtualIpIds,
  storyboardReferenceSelection,
  generationTasks,
  currentClipId,
  videoModels,
  videoModelsLoading,
  generatingStoryboard,
  generatingKeyframes,
  submitting,
  submitError,
  canGenerateStoryboard,
  canGenerateKeyframes,
  canSubmit,
  onActionChange,
  onPromptChange,
  onModelChange,
  onDurationChange,
  onResolutionChange,
  onRatioChange,
  onReasonChange,
  onVideoReferenceChoiceChange,
  onReferenceImagesInputChange,
  onStoryboardStyleChange,
  onStoryboardPanelCountChange,
  onStoryboardVirtualIpToggle,
  onGenerateStoryboard,
  onGenerateKeyframes,
  onSubmit,
}: {
  action: TimelineClipVideoReworkAction;
  prompt: string;
  model: string;
  duration: string;
  resolution: string;
  ratio: string;
  reason: string;
  videoReferenceChoice: TimelineVideoReferenceChoice;
  referenceImagesInput: string;
  keyframeStatus: { startReady: boolean; endReady: boolean; label: string };
  manualReferenceAvailable: boolean;
  storyboardStyle: "2d_cartoon" | "3d_cartoon" | "live_action";
  storyboardPanelCount: string;
  storyboardPanelIndex?: number | null;
  storyboardSheetUrl?: string | null;
  episodeCharacters: EpisodeCharacter[];
  episodeCharactersLoading: boolean;
  episodeCharactersError: string | null;
  onNavigateToCharacters?: () => void;
  selectedStoryboardVirtualIpIds: number[];
  storyboardReferenceSelection: TimelineClipStoryboardReferenceSelection;
  generationTasks?: ClipGenerationTaskMap;
  currentClipId?: string | null;
  videoModels?: VideoModelOption[];
  videoModelsLoading?: boolean;
  generatingStoryboard: boolean;
  generatingKeyframes: boolean;
  submitting: boolean;
  submitError: string | null;
  canGenerateStoryboard: boolean;
  canGenerateKeyframes: boolean;
  canSubmit: boolean;
  onActionChange: (value: TimelineClipVideoReworkAction) => void;
  onPromptChange: (value: string) => void;
  onModelChange: (value: string) => void;
  onDurationChange: (value: string) => void;
  onResolutionChange: (value: string) => void;
  onRatioChange: (value: string) => void;
  onReasonChange: (value: string) => void;
  onVideoReferenceChoiceChange: (value: TimelineVideoReferenceChoice) => void;
  onReferenceImagesInputChange: (value: string) => void;
  onStoryboardStyleChange: (
    value: "2d_cartoon" | "3d_cartoon" | "live_action",
  ) => void;
  onStoryboardPanelCountChange: (value: string) => void;
  onStoryboardVirtualIpToggle: (virtualIpId: number, checked: boolean) => void;
  onGenerateStoryboard: () => void;
  onGenerateKeyframes: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <form
      data-clip-command-rail="compact"
      data-clip-command-layout="compact-video-primary"
      className="px-0.5 py-0"
      onSubmit={onSubmit}
    >
      <TimelineClipSharedReferenceContext
        episodeCharacters={episodeCharacters}
        selectedCharacterVirtualIpIds={selectedStoryboardVirtualIpIds}
        selectedCharacterReferenceUrls={
          storyboardReferenceSelection.selectedStoryboardCharacterReferenceImages
        }
        selectedEnvironmentReferenceUrls={
          storyboardReferenceSelection.selectedStoryboardEnvironmentReferenceImages
        }
        manualReferenceImages={referenceImagesInput}
        onManualReferenceImagesChange={onReferenceImagesInputChange}
      />
      <div
        data-clip-command-surface="action-tray"
        data-clip-command-surface-style="flat-action-cluster"
        data-clip-command-density="readable"
        className={COMMAND_SURFACE_CLASS}
      >
        <div className={COMMAND_GRID_CLASS}>
          <StoryboardReferenceCard
            storyboardStyle={storyboardStyle}
            storyboardPanelCount={storyboardPanelCount}
            storyboardSheetUrl={storyboardSheetUrl}
            episodeCharacters={episodeCharacters}
            episodeCharactersLoading={episodeCharactersLoading}
            episodeCharactersError={episodeCharactersError}
            onNavigateToCharacters={onNavigateToCharacters}
            selectedCharacterVirtualIpIds={selectedStoryboardVirtualIpIds}
            storyboardReferenceSelection={storyboardReferenceSelection}
            generatingStoryboard={generatingStoryboard}
            canGenerateStoryboard={canGenerateStoryboard}
            storyboardTask={generationTasks?.storyboard}
            currentClipId={currentClipId ?? null}
            onStoryboardStyleChange={onStoryboardStyleChange}
            onStoryboardPanelCountChange={onStoryboardPanelCountChange}
            onCharacterVirtualIpToggle={onStoryboardVirtualIpToggle}
            onGenerateStoryboard={onGenerateStoryboard}
          />
          <TimelineClipKeyframeCard
            generating={generatingKeyframes}
            canGenerate={canGenerateKeyframes}
            keyframeStatus={keyframeStatus}
            keyframesTask={generationTasks?.keyframes}
            currentClipId={currentClipId ?? null}
            onGenerate={onGenerateKeyframes}
          />

          <TimelineClipVideoReworkCard
            action={action}
            prompt={prompt}
            model={model}
            duration={duration}
            resolution={resolution}
            ratio={ratio}
            reason={reason}
            videoReferenceChoice={videoReferenceChoice}
            storyboardPanelIndex={storyboardPanelIndex}
            startEndReferenceAvailable={keyframeStatus.startReady}
            manualReferenceAvailable={manualReferenceAvailable}
            episodeCharacters={episodeCharacters}
            selectedCharacterVirtualIpIds={selectedStoryboardVirtualIpIds}
            selectedCharacterReferenceUrls={
              storyboardReferenceSelection.selectedStoryboardCharacterReferenceImages
            }
            selectedEnvironmentReferenceUrls={
              storyboardReferenceSelection.selectedStoryboardEnvironmentReferenceImages
            }
            submitting={submitting}
            submitError={submitError}
            canSubmit={canSubmit}
            videoTask={generationTasks?.video}
            currentClipId={currentClipId ?? null}
            videoModels={videoModels}
            videoModelsLoading={videoModelsLoading}
            onActionChange={onActionChange}
            onPromptChange={onPromptChange}
            onModelChange={onModelChange}
            onDurationChange={onDurationChange}
            onResolutionChange={onResolutionChange}
            onRatioChange={onRatioChange}
            onReasonChange={onReasonChange}
            onVideoReferenceChoiceChange={onVideoReferenceChoiceChange}
          />
        </div>
      </div>
    </form>
  );
}
