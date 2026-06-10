"use client";

import { useState } from "react";
import { timelineAPI } from "@/utils/api/endpoints";
import type { TimelineClipStoryboardStyle } from "@/utils/api/types";
import {
  buildTimelineClipKeyframeGeneratePayload,
  buildTimelineClipStoryboardGeneratePayload,
} from "./TimelineClipProviderGenerationPayloads";
import { parseOptionalNumber } from "./TimelineClipProviderReworkModel";
import type { NotifyVariant } from "./TimelineClipProviderReworkControlsTypes";
import type { ClipGenerationTaskKind } from "./useTimelineClipGenerationTaskTracker";

export function useTimelineClipProviderGenerationActions({
  timelineId,
  timelineVersion,
  clipId,
  prompt,
  model,
  storyboardStyle,
  storyboardPanelCount,
  referenceImages,
  selectedVirtualIpIds,
  selectedCharacterReferenceImages,
  selectedEnvironmentReferenceImages,
  onTaskQueued,
  onNotify,
}: {
  timelineId?: number | string | null;
  timelineVersion?: number | null;
  clipId?: string | null;
  prompt: string;
  model: string;
  storyboardStyle: TimelineClipStoryboardStyle;
  storyboardPanelCount: string;
  referenceImages: string[];
  selectedVirtualIpIds: number[];
  selectedCharacterReferenceImages: string[];
  selectedEnvironmentReferenceImages: string[];
  onTaskQueued?: (kind: ClipGenerationTaskKind, taskId: number) => void;
  onNotify?: (message: string, variant: NotifyVariant) => void;
}) {
  const [generatingStoryboard, setGeneratingStoryboard] = useState(false);
  const [generatingKeyframes, setGeneratingKeyframes] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const canGenerateStoryboard = Boolean(
    timelineId && timelineVersion && clipId && !generatingStoryboard,
  );
  const canGenerateKeyframes = Boolean(
    timelineId && timelineVersion && clipId && !generatingKeyframes,
  );

  const handleGenerateStoryboard = async () => {
    if (!timelineId || !timelineVersion || !clipId) {
      return warnMissingContext(setSubmitError, onNotify);
    }
    const panelCount = parseOptionalNumber(storyboardPanelCount) ?? 4;
    setGeneratingStoryboard(true);
    setSubmitError(null);
    try {
      const res = await timelineAPI.generateTimelineClipStoryboard(
        timelineId,
        clipId,
        buildTimelineClipStoryboardGeneratePayload({
          expectedVersion: timelineVersion,
          panelCount,
          style: storyboardStyle,
          referenceImages,
          characterVirtualIpIds: selectedVirtualIpIds,
          characterReferenceImages: selectedCharacterReferenceImages,
          environmentReferenceImages: selectedEnvironmentReferenceImages,
        }),
      );
      if (!res.success || !res.data) {
        return reportError(
          res.error || "提交故事板任务失败",
          setSubmitError,
          onNotify,
        );
      }
      onNotify?.(`故事板任务已提交 #${res.data.task_id}，生成中…`, "success");
      onTaskQueued?.("storyboard", res.data.task_id);
    } finally {
      setGeneratingStoryboard(false);
    }
  };

  const handleGenerateKeyframes = async () => {
    if (!timelineId || !timelineVersion || !clipId) {
      return warnMissingContext(setSubmitError, onNotify);
    }
    setGeneratingKeyframes(true);
    setSubmitError(null);
    try {
      const res = await timelineAPI.generateTimelineClipKeyframes(
        timelineId,
        clipId,
        buildTimelineClipKeyframeGeneratePayload({
          expectedVersion: timelineVersion,
          prompt,
          model,
          referenceImages,
          characterVirtualIpIds: selectedVirtualIpIds,
          characterReferenceImages: selectedCharacterReferenceImages,
          environmentReferenceImages: selectedEnvironmentReferenceImages,
        }),
      );
      if (!res.success || !res.data) {
        return reportError(
          res.error || "提交首尾帧任务失败",
          setSubmitError,
          onNotify,
        );
      }
      onNotify?.(`首尾帧任务已提交 #${res.data.task_id}，生成中…`, "success");
      onTaskQueued?.("keyframes", res.data.task_id);
    } finally {
      setGeneratingKeyframes(false);
    }
  };

  return {
    generatingStoryboard,
    generatingKeyframes,
    submitError,
    setSubmitError,
    canGenerateStoryboard,
    canGenerateKeyframes,
    handleGenerateStoryboard,
    handleGenerateKeyframes,
  };
}

function warnMissingContext(
  setSubmitError: (message: string) => void,
  onNotify?: (message: string, variant: NotifyVariant) => void,
) {
  const message = "当前片段缺少稳定 Timeline 上下文";
  setSubmitError(message);
  onNotify?.(message, "warning");
}

function reportError(
  message: string,
  setSubmitError: (message: string) => void,
  onNotify?: (message: string, variant: NotifyVariant) => void,
) {
  setSubmitError(message);
  onNotify?.(message, "error");
}
