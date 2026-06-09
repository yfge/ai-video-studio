"use client";

import type { FormEvent } from "react";
import type {
  EpisodeCharacter,
  TimelineClipVideoReworkAction,
} from "@/utils/api/types";
import { StoryboardReferenceCard } from "./TimelineClipProviderReworkCardSections";
import { TimelineClipVideoReworkCard } from "./TimelineClipVideoReworkCard";
import type { TimelineVideoReferenceChoice } from "./TimelineClipProviderReworkModel";
import type { TimelineClipStoryboardReferenceSelection } from "./useTimelineClipStoryboardReferenceSelection";

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
  selectedStoryboardVirtualIpIds,
  storyboardReferenceSelection,
  generatingStoryboard,
  submitting,
  submitError,
  canGenerateStoryboard,
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
  selectedStoryboardVirtualIpIds: number[];
  storyboardReferenceSelection: TimelineClipStoryboardReferenceSelection;
  generatingStoryboard: boolean;
  submitting: boolean;
  submitError: string | null;
  canGenerateStoryboard: boolean;
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
          selectedCharacterVirtualIpIds={selectedStoryboardVirtualIpIds}
          storyboardReferenceSelection={storyboardReferenceSelection}
          generatingStoryboard={generatingStoryboard}
          canGenerateStoryboard={canGenerateStoryboard}
          onReferenceImagesInputChange={onReferenceImagesInputChange}
          onStoryboardStyleChange={onStoryboardStyleChange}
          onStoryboardPanelCountChange={onStoryboardPanelCountChange}
          onCharacterVirtualIpToggle={onStoryboardVirtualIpToggle}
          onGenerateStoryboard={onGenerateStoryboard}
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
          submitting={submitting}
          submitError={submitError}
          canSubmit={canSubmit}
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
