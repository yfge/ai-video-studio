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
  parseOptionalNumber,
  type TimelineVideoReferenceChoice,
} from "./TimelineClipProviderReworkModel";
import { timelineClipProductionReadiness } from "./TimelineClipProductionReadiness";
import { useTimelineClipStoryboardReferenceSelection } from "./useTimelineClipStoryboardReferenceSelection";
import { useTimelineClipStoryboardVirtualIpSelection } from "./useTimelineClipStoryboardVirtualIpSelection";
import { useTimelineClipProviderGenerationActions } from "./useTimelineClipProviderGenerationActions";
import { useTimelineClipGenerationTaskTracker } from "./useTimelineClipGenerationTaskTracker";
import type { TimelineClipProviderReworkControlsProps } from "./TimelineClipProviderReworkControlsTypes";

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
  const [duration, setDuration] = useState("");
  const [resolution, setResolution] = useState("720p");
  const [ratio, setRatio] = useState("");
  const [reason, setReason] = useState("");
  const [videoReferenceChoice, setVideoReferenceChoice] =
    useState<TimelineVideoReferenceChoice>("start_end");
  const [referenceImagesInput, setReferenceImagesInput] = useState("");
  const [storyboardModel, setStoryboardModel] = useState("");
  const [storyboardStyle, setStoryboardStyle] =
    useState<TimelineClipStoryboardStyle>("live_action");
  const [storyboardPanelCount, setStoryboardPanelCount] = useState("4");
  const [operatorReviewed, setOperatorReviewed] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const isVideoClip = isTimelineVideoClip(item);
  useEffect(() => setOperatorReviewed(false), [clipId]);
  const productionReadiness = timelineClipProductionReadiness(item, operatorReviewed);
  const parsedDuration = parseOptionalNumber(duration);
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
  let effectiveReferenceChoice = videoReferenceChoice;
  if (
    effectiveReferenceChoice === "clip_storyboard_panel" &&
    !productionReadiness.storyboardPanelIndex
  ) {
    effectiveReferenceChoice = "start_end";
  }
  const canSubmit = Boolean(
    timelineId && timelineVersion && clipId && productionReadiness.canGenerateVideo && !submitting,
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
    if (duration.trim() && !parsedDuration) {
      const message = "请输入有效的视频时长";
      generationActions.setSubmitError(message);
      onNotify?.(message, "warning");
      return;
    }
    if (!productionReadiness.canGenerateVideo) {
      const message =
        productionReadiness.videoGateMessage ||
        "先完成片段分镜图和首尾帧后才能生视频";
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
      duration: parsedDuration,
      resolution,
      ratio,
      reason,
      referenceChoice: effectiveReferenceChoice,
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
      duration={duration}
      resolution={resolution}
      ratio={ratio}
      reason={reason}
      videoReferenceChoice={videoReferenceChoice}
      referenceImagesInput={referenceImagesInput}
      operatorReviewed={operatorReviewed}
      productionReadiness={productionReadiness}
      manualReferenceAvailable
      storyboardModel={storyboardModel}
      storyboardStyle={storyboardStyle}
      storyboardPanelCount={storyboardPanelCount}
      storyboardPanelIndex={productionReadiness.storyboardPanelIndex}
      storyboardSheetUrl={productionReadiness.storyboardSheetUrl}
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
      onDurationChange={setDuration}
      onResolutionChange={setResolution}
      onRatioChange={setRatio}
      onReasonChange={setReason}
      onVideoReferenceChoiceChange={setVideoReferenceChoice}
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
