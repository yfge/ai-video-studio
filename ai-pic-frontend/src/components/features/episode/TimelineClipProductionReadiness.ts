import type { TimelineItem } from "@/components/features";
import {
  timelineClipHasShotPlan,
  timelineClipHumanReview,
  timelineClipStartEndFrameStatus,
  timelineClipStoryboardPanelIndex,
  timelineClipStoryboardSheetUrl,
} from "./TimelineClipProviderReworkModel";

export interface TimelineClipProductionReadiness {
  storyboardReady: boolean;
  keyframesReady: boolean;
  canGenerateVideo: boolean;
  videoGateMessage: string | null;
  humanReviewRequired: boolean;
  humanReviewReady: boolean;
  humanReviewLabel: string;
  storyboardPanelIndex: number | null;
  storyboardSheetUrl: string | null;
  keyframeStatus: { startReady: boolean; endReady: boolean; label: string };
}

export const VIDEO_IMAGE_GATE_MESSAGE =
  "先生成片段宫格故事板或首尾帧后才能生视频";

export function timelineClipProductionReadiness(
  item: TimelineItem | null,
  operatorReviewed = false,
): TimelineClipProductionReadiness {
  const storyboardPanelIndex = timelineClipStoryboardPanelIndex(item);
  const storyboardSheetUrl = timelineClipStoryboardSheetUrl(item);
  const keyframeStatus = timelineClipStartEndFrameStatus(item);
  const storyboardReady = Boolean(storyboardSheetUrl);
  const keyframesReady = keyframeStatus.startReady && keyframeStatus.endReady;
  const humanReview = timelineClipHumanReview(item);
  const humanReviewReady =
    !humanReview.required || humanReview.approved || operatorReviewed;
  const imageReady =
    storyboardReady || keyframesReady || timelineClipHasShotPlan(item);
  const canGenerateVideo = imageReady && humanReviewReady;
  let videoGateMessage: string | null = null;
  if (!canGenerateVideo) {
    videoGateMessage = humanReviewReady
      ? VIDEO_IMAGE_GATE_MESSAGE
      : "先完成人工复核";
  }
  return {
    storyboardReady,
    keyframesReady,
    canGenerateVideo,
    videoGateMessage,
    humanReviewRequired: humanReview.required,
    humanReviewReady,
    humanReviewLabel: humanReviewReady ? "人工复核已确认" : "待人工复核",
    storyboardPanelIndex,
    storyboardSheetUrl,
    keyframeStatus,
  };
}
