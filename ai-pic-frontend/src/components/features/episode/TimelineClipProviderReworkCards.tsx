"use client";

import type { FormEvent } from "react";
import type {
  EpisodeCharacter,
  TimelineClipVideoReworkAction,
} from "@/utils/api/types";
import { TimelineClipKeyframeCard } from "./TimelineClipKeyframeCard";
import { StoryboardReferenceCard } from "./TimelineClipProviderReworkCardSections";
import { TimelineClipVideoReworkCard } from "./TimelineClipVideoReworkCard";
import type { TimelineVideoReferenceChoice } from "./TimelineClipProviderReworkModel";
import type { TimelineClipStoryboardReferenceSelection } from "./useTimelineClipStoryboardReferenceSelection";
import type { ClipGenerationTaskMap } from "./useTimelineClipGenerationTaskTracker";
import type { VideoModelOption } from "./TimelineClipProviderReworkControlsTypes";

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
    <form className="mt-3 border-t border-gray-100 pt-3" onSubmit={onSubmit}>
      <div className="grid gap-3">
        <StoryboardReferenceCard
          referenceImagesInput={referenceImagesInput}
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
          onReferenceImagesInputChange={onReferenceImagesInputChange}
          onStoryboardStyleChange={onStoryboardStyleChange}
          onStoryboardPanelCountChange={onStoryboardPanelCountChange}
          onCharacterVirtualIpToggle={onStoryboardVirtualIpToggle}
          onGenerateStoryboard={onGenerateStoryboard}
        />

        <TimelineClipKeyframeCard
          generating={generatingKeyframes}
          canGenerate={canGenerateKeyframes}
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
    </form>
  );
}
