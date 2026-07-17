"use client";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { timelineAPI } from "@/utils/api/endpoints";
import type { Environment, EpisodeCharacter } from "@/utils/api/types";
import type {
  TimelineClipStoryboardStyle,
  TimelineClipVideoReworkAction,
} from "@/utils/api/types";
import { TimelineClipProviderReworkCards } from "./TimelineClipProviderReworkCards";
import {
  buildTimelineClipVideoReworkTaskPayload,
  isTimelineVideoClip,
  parseReferenceImagesInput,
} from "./TimelineClipProviderReworkModel";
import {
  timelineClipProductionReadiness,
  VIDEO_IMAGE_GATE_MESSAGE,
} from "./TimelineClipProductionReadiness";
import { useTimelineClipStoryboardReferenceSelection } from "./useTimelineClipStoryboardReferenceSelection";
import { useTimelineClipStoryboardVirtualIpSelection } from "./useTimelineClipStoryboardVirtualIpSelection";
import { useTimelineClipProviderGenerationActions } from "./useTimelineClipProviderGenerationActions";
import { useTimelineClipGenerationTaskTracker } from "./useTimelineClipGenerationTaskTracker";
import type { TimelineClipProviderReworkControlsProps } from "./TimelineClipProviderReworkControlsTypes";
import { useTimelineClipVideoReferenceChoice } from "./useTimelineClipVideoReferenceChoice";
const EMPTY_EPISODE_CHARACTERS: EpisodeCharacter[] = [];
const EMPTY_ENVIRONMENTS: Environment[] = [];
export function TimelineClipProviderReworkControls({
  timelineId,
  timelineVersion,
  clipId,
  item,
  episodeId = null,
  episodeCharacters = EMPTY_EPISODE_CHARACTERS,
  episodeCharactersLoading = false,
  episodeCharactersError = null,
  environments = EMPTY_ENVIRONMENTS,
  selectedEnvironmentId = null,
  storyboardCharacterImageOptions,
  storyboardEnvironmentImageOptions,
  imageModels,
  imageModelsLoading,
  videoModels,
  videoModelsLoading,
  onNavigateToCharacters,
  onQueued,
  onGenerationCompleted,
  onNotify,
}: TimelineClipProviderReworkControlsProps) {
  const [action, setAction] = useState<TimelineClipVideoReworkAction>("re_cut");
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState("");
  const [resolution, setResolution] = useState("720p");
  const [ratio, setRatio] = useState("");
  const [reason, setReason] = useState("");
  const [referenceImagesInput, setReferenceImagesInput] = useState("");
  const [storyboardModel, setStoryboardModel] = useState("");
  const [storyboardStyle, setStoryboardStyle] =
    useState<TimelineClipStoryboardStyle>("live_action");
  const [storyboardPanelCount, setStoryboardPanelCount] = useState("auto");
  const [operatorReviewed, setOperatorReviewed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const isVideoClip = isTimelineVideoClip(item);
  useEffect(() => setOperatorReviewed(false), [clipId]);
  const productionReadiness = timelineClipProductionReadiness(
    item,
    operatorReviewed,
  );
  const videoReference = useTimelineClipVideoReferenceChoice(
    clipId,
    productionReadiness.storyboardReady,
  );
  const targetDurationSeconds = item
    ? Math.max((item.endMs - item.startMs) / 1000, 0.1)
    : null;
  const referenceImages = parseReferenceImagesInput(referenceImagesInput);
  const { selectedStoryboardVirtualIpIds, handleStoryboardVirtualIpToggle } =
    useTimelineClipStoryboardVirtualIpSelection({
      item,
      episodeCharacters,
    });
  const storyboardReferenceSelection =
    useTimelineClipStoryboardReferenceSelection({
      episodeId,
      episodeCharacters,
      environments,
      selectedEnvironmentId,
      selectedStoryboardVirtualIpIds,
      storyboardCharacterImageOptions,
      storyboardEnvironmentImageOptions,
    });
  const selectedCharacterReferenceImages =
    storyboardReferenceSelection.selectedStoryboardCharacterReferenceImages;
  const selectedEnvironmentReferenceImages =
    storyboardReferenceSelection.selectedStoryboardEnvironmentReferenceImages;
  const taskTracker = useTimelineClipGenerationTaskTracker({
    onCompleted: async () => {
      await onGenerationCompleted?.();
      await onQueued?.();
    },
    onNotify,
  });
  const generationActions = useTimelineClipProviderGenerationActions({
    timelineId,
    timelineVersion,
    clipId,
    prompt,
    model,
    storyboardModel,
    storyboardStyle,
    storyboardPanelCount,
    referenceImages,
    selectedVirtualIpIds: selectedStoryboardVirtualIpIds,
    selectedCharacterReferenceImages,
    selectedEnvironmentReferenceImages,
    onTaskQueued: (kind, taskId) =>
      taskTracker.track(kind, taskId, clipId ?? null),
    onNotify,
  });
  const canSubmit = Boolean(
    timelineId &&
      timelineVersion &&
      clipId &&
      productionReadiness.canGenerateVideo &&
      !submitting,
  );

  if (!isVideoClip) return null;
  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!timelineId || !timelineVersion || !clipId) {
      const message = "当前片段缺少稳定 Timeline 上下文";
      generationActions.setSubmitError(message);
      onNotify?.(message, "warning");
      return;
    }
    if (!productionReadiness.canGenerateVideo) {
      const message =
        productionReadiness.videoGateMessage || VIDEO_IMAGE_GATE_MESSAGE;
      generationActions.setSubmitError(message);
      onNotify?.(message, "warning");
      return;
    }

    setSubmitting(true);
    generationActions.setSubmitError(null);
    const payload = buildTimelineClipVideoReworkTaskPayload({
      expectedVersion: timelineVersion,
      action,
      prompt,
      model,
      resolution,
      ratio,
      reason,
      referenceChoice: videoReference.effectiveChoice,
      referenceImages,
      operatorReviewed,
      characterVirtualIpIds: selectedStoryboardVirtualIpIds,
      characterReferenceImages:
        storyboardReferenceSelection.selectedStoryboardCharacterReferenceImages,
      environmentReferenceImages:
        storyboardReferenceSelection.selectedStoryboardEnvironmentReferenceImages,
    });
    try {
      const res = await timelineAPI.queueTimelineClipVideoRework(
        timelineId,
        clipId,
        payload,
      );
      if (!res.success || !res.data) {
        const message = res.error || "提交视频重做任务失败";
        generationActions.setSubmitError(message);
        onNotify?.(message, "error");
        return;
      }
      setPrompt("");
      setReason("");
      await onQueued?.();
      onNotify?.(`视频重做任务已提交 #${res.data.task_id}，生成中…`, "success");
      taskTracker.track("video", res.data.task_id, clipId ?? null);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <TimelineClipProviderReworkCards
      action={action}
      prompt={prompt}
      model={model}
      targetDurationSeconds={targetDurationSeconds}
      resolution={resolution}
      ratio={ratio}
      reason={reason}
      videoReferenceChoice={videoReference.choice}
      referenceImagesInput={referenceImagesInput}
      operatorReviewed={operatorReviewed}
      productionReadiness={productionReadiness}
      manualReferenceAvailable
      storyboardModel={storyboardModel}
      storyboardStyle={storyboardStyle}
      storyboardPanelCount={storyboardPanelCount}
      storyboardAvailable={productionReadiness.storyboardReady}
      episodeCharacters={episodeCharacters}
      episodeCharactersLoading={episodeCharactersLoading}
      episodeCharactersError={episodeCharactersError}
      onNavigateToCharacters={onNavigateToCharacters}
      selectedStoryboardVirtualIpIds={selectedStoryboardVirtualIpIds}
      storyboardReferenceSelection={storyboardReferenceSelection}
      generationTasks={taskTracker.tasks}
      currentClipId={clipId ?? null}
      imageModels={imageModels}
      imageModelsLoading={imageModelsLoading}
      videoModels={videoModels}
      videoModelsLoading={videoModelsLoading}
      generatingStoryboard={generationActions.generatingStoryboard}
      generatingKeyframes={generationActions.generatingKeyframes}
      submitting={submitting}
      submitError={generationActions.submitError}
      canGenerateStoryboard={generationActions.canGenerateStoryboard}
      canGenerateKeyframes={generationActions.canGenerateKeyframes}
      canSubmit={canSubmit}
      onActionChange={setAction}
      onPromptChange={setPrompt}
      onModelChange={setModel}
      onResolutionChange={setResolution}
      onRatioChange={setRatio}
      onReasonChange={setReason}
      onVideoReferenceChoiceChange={videoReference.setChoice}
      onReferenceImagesInputChange={setReferenceImagesInput}
      onOperatorReviewedChange={setOperatorReviewed}
      onStoryboardModelChange={setStoryboardModel}
      onStoryboardStyleChange={setStoryboardStyle}
      onStoryboardPanelCountChange={setStoryboardPanelCount}
      onStoryboardVirtualIpToggle={handleStoryboardVirtualIpToggle}
      onGenerateStoryboard={generationActions.handleGenerateStoryboard}
      onGenerateKeyframes={generationActions.handleGenerateKeyframes}
      onSubmit={handleSubmit}
    />
  );
}
