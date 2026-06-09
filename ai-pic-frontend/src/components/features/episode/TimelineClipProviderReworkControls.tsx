"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { timelineAPI } from "@/utils/api/endpoints";
import type {
  Environment,
  EpisodeCharacter,
  TimelineClipStoryboardStyle,
  TimelineClipVideoReworkAction,
} from "@/utils/api/types";
import { TimelineClipProviderReworkCards } from "./TimelineClipProviderReworkCards";
import {
  buildTimelineClipVideoReworkTaskPayload,
  isTimelineVideoClip,
  parseReferenceImagesInput,
  parseOptionalNumber,
  timelineClipStoryboardPanelIndex,
  timelineClipStoryboardSheetUrl,
  type TimelineVideoReferenceChoice,
} from "./TimelineClipProviderReworkModel";
import { useTimelineClipStoryboardReferenceSelection } from "./useTimelineClipStoryboardReferenceSelection";
import { useTimelineClipStoryboardVirtualIpSelection } from "./useTimelineClipStoryboardVirtualIpSelection";
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
  onQueued,
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
  const [storyboardStyle, setStoryboardStyle] =
    useState<TimelineClipStoryboardStyle>("live_action");
  const [storyboardPanelCount, setStoryboardPanelCount] = useState("4");
  const [generatingStoryboard, setGeneratingStoryboard] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const isVideoClip = isTimelineVideoClip(item);
  const storyboardPanelIndex = timelineClipStoryboardPanelIndex(item);
  const storyboardSheetUrl = timelineClipStoryboardSheetUrl(item);
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
  const effectiveReferenceChoice =
    videoReferenceChoice === "clip_storyboard_panel" && !storyboardPanelIndex
      ? "start_end"
      : videoReferenceChoice;
  const canSubmit = Boolean(
    timelineId && timelineVersion && clipId && !submitting,
  );
  const canGenerateStoryboard = Boolean(
    timelineId && timelineVersion && clipId && !generatingStoryboard,
  );

  if (!isVideoClip) return null;

  const handleGenerateStoryboard = async () => {
    if (!timelineId || !timelineVersion || !clipId) {
      const message = "当前片段缺少稳定 Timeline 上下文";
      setSubmitError(message);
      onNotify?.(message, "warning");
      return;
    }
    const panelCount = parseOptionalNumber(storyboardPanelCount) ?? 4;
    setGeneratingStoryboard(true);
    setSubmitError(null);
    try {
      const res = await timelineAPI.generateTimelineClipStoryboard(
        timelineId,
        clipId,
        {
          expected_version: timelineVersion,
          panel_count: Math.min(9, Math.max(2, Math.round(panelCount))),
          style: storyboardStyle,
          generation_profile: "clip_storyboard",
          size: "1536x1536",
          aspect_ratio: "1:1",
          reference_images: referenceImages.length
            ? referenceImages
            : undefined,
          character_virtual_ip_ids: selectedStoryboardVirtualIpIds.length
            ? selectedStoryboardVirtualIpIds
            : undefined,
          character_reference_images: storyboardReferenceSelection
            .selectedStoryboardCharacterReferenceImages.length
            ? storyboardReferenceSelection.selectedStoryboardCharacterReferenceImages
            : undefined,
          environment_reference_images: storyboardReferenceSelection
            .selectedStoryboardEnvironmentReferenceImages.length
            ? storyboardReferenceSelection.selectedStoryboardEnvironmentReferenceImages
            : undefined,
        },
      );
      if (!res.success || !res.data) {
        const message = res.error || "提交故事板任务失败";
        setSubmitError(message);
        onNotify?.(message, "error");
        return;
      }
      onNotify?.(`故事板任务已提交 #${res.data.task_id}`, "success");
    } finally {
      setGeneratingStoryboard(false);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!timelineId || !timelineVersion || !clipId) {
      const message = "当前片段缺少稳定 Timeline 上下文";
      setSubmitError(message);
      onNotify?.(message, "warning");
      return;
    }
    if (duration.trim() && !parsedDuration) {
      const message = "请输入有效的视频时长";
      setSubmitError(message);
      onNotify?.(message, "warning");
      return;
    }

    setSubmitting(true);
    setSubmitError(null);
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
    });
    try {
      const res = await timelineAPI.queueTimelineClipVideoRework(
        timelineId,
        clipId,
        payload,
      );
      if (!res.success || !res.data) {
        const message = res.error || "提交视频重做任务失败";
        setSubmitError(message);
        onNotify?.(message, "error");
        return;
      }
      setPrompt("");
      setReason("");
      await onQueued?.();
      onNotify?.(`视频重做任务已提交 #${res.data.task_id}`, "success");
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
      storyboardStyle={storyboardStyle}
      storyboardPanelCount={storyboardPanelCount}
      storyboardPanelIndex={storyboardPanelIndex}
      storyboardSheetUrl={storyboardSheetUrl}
      episodeCharacters={episodeCharacters}
      episodeCharactersLoading={episodeCharactersLoading}
      episodeCharactersError={episodeCharactersError}
      selectedStoryboardVirtualIpIds={selectedStoryboardVirtualIpIds}
      storyboardReferenceSelection={storyboardReferenceSelection}
      generatingStoryboard={generatingStoryboard}
      submitting={submitting}
      submitError={submitError}
      canGenerateStoryboard={canGenerateStoryboard}
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
      onStoryboardStyleChange={setStoryboardStyle}
      onStoryboardPanelCountChange={setStoryboardPanelCount}
      onStoryboardVirtualIpToggle={handleStoryboardVirtualIpToggle}
      onGenerateStoryboard={handleGenerateStoryboard}
      onSubmit={handleSubmit}
    />
  );
}
