import type { TimelineItem } from "@/components/features";
import { asRecord, getString } from "@/hooks/useEpisodeDetail";
import type {
  TimelineClipVideoReferenceMode,
  TimelineClipVideoReworkAction,
  TimelineClipVideoReworkTaskRequest,
} from "@/utils/api/types";
import { timelineItemMeta } from "./EpisodeTimelineWorkspaceModel";
import { dedupeVirtualIpIds } from "./TimelineClipCharacterContextModel";

export {
  dedupeVirtualIpIds,
  sameVirtualIpIds,
  timelineClipCharacterNames,
  timelineClipCharacterVirtualIpIds,
} from "./TimelineClipCharacterContextModel";

export type TimelineVideoReferenceChoice =
  | TimelineClipVideoReferenceMode
  | "manual_refs";

export function isTimelineVideoClip(item: TimelineItem | null) {
  const meta = timelineItemMeta(item);
  return item?.type === "video" || getString(meta.track_type) === "video";
}

export function buildTimelineClipVideoReworkTaskPayload({
  expectedVersion,
  action,
  prompt,
  model,
  duration,
  resolution,
  ratio,
  reason,
  referenceChoice = "start_end",
  referenceImages,
  useClipStoryboard,
  characterVirtualIpIds,
  characterReferenceImages,
  environmentReferenceImages,
  operatorReviewed,
}: {
  expectedVersion: number;
  action: TimelineClipVideoReworkAction;
  prompt?: string | null;
  model?: string | null;
  duration?: number | null;
  resolution?: string | null;
  ratio?: string | null;
  reason?: string | null;
  referenceChoice?: TimelineVideoReferenceChoice;
  referenceImages?: string[] | null;
  useClipStoryboard?: boolean;
  characterVirtualIpIds?: number[] | null;
  characterReferenceImages?: string[] | null;
  environmentReferenceImages?: string[] | null;
  operatorReviewed?: boolean;
}): TimelineClipVideoReworkTaskRequest {
  const payload: TimelineClipVideoReworkTaskRequest = {
    expected_version: expectedVersion,
    action,
    resolution: resolution?.trim() || "720p",
    asset_role: "generated_video",
    use_end_frame: true,
    return_last_frame: true,
  };
  const cleanedPrompt = prompt?.trim();
  if (cleanedPrompt) payload.prompt = cleanedPrompt;
  const cleanedModel = model?.trim();
  if (cleanedModel) payload.model = cleanedModel;
  if (duration && Number.isFinite(duration) && duration > 0) {
    payload.duration = duration;
  }
  const cleanedRatio = ratio?.trim();
  if (cleanedRatio) payload.ratio = cleanedRatio;
  const cleanedReason = reason?.trim();
  if (cleanedReason) payload.reason = cleanedReason;
  const cleanedRefs = dedupeReferenceImages(referenceImages);
  if (useClipStoryboard || referenceChoice === "clip_storyboard_sheet") {
    payload.reference_mode = "clip_storyboard_sheet";
    payload.use_clip_storyboard = true;
    payload.use_end_frame = false;
  } else if (referenceChoice === "clip_storyboard_panel") {
    payload.reference_mode = "clip_storyboard_panel";
    payload.use_clip_storyboard = true;
    payload.use_end_frame = false;
  } else if (referenceChoice === "manual_refs") {
    payload.reference_mode = "start_end";
    payload.use_end_frame = false;
  }
  if (cleanedRefs.length > 0) {
    payload.reference_images = cleanedRefs;
  }
  const cleanedCharacterIds = dedupeVirtualIpIds(characterVirtualIpIds || []);
  if (cleanedCharacterIds.length > 0) {
    payload.character_virtual_ip_ids = cleanedCharacterIds;
  }
  const cleanedCharacterRefs = dedupeReferenceImages(characterReferenceImages);
  if (cleanedCharacterRefs.length > 0) {
    payload.character_reference_images = cleanedCharacterRefs;
  }
  const cleanedEnvironmentRefs = dedupeReferenceImages(
    environmentReferenceImages,
  );
  if (cleanedEnvironmentRefs.length > 0) {
    payload.environment_reference_images = cleanedEnvironmentRefs;
  }
  if (operatorReviewed) {
    payload.operator_reviewed = true;
  }
  return payload;
}

export function timelineClipHumanReview(item: TimelineItem | null) {
  const meta = timelineItemMeta(item);
  const sourceRefs = asRecord(meta.source_refs);
  const review = asRecord(sourceRefs?.human_review);
  const required = review?.required === true;
  const status = getString(review?.status)?.toLowerCase() ?? "";
  const approved = ["approved", "confirmed", "passed"].includes(status);
  return { required, approved };
}

export function timelineClipStoryboardPanelIndex(item: TimelineItem | null) {
  const meta = timelineItemMeta(item);
  const sourceRefs = asRecord(meta.source_refs);
  const storyboard = asRecord(sourceRefs?.clip_storyboard);
  const raw =
    storyboard?.panel_index ??
    asRecord(meta.clip_storyboard_sheet_asset_ref)?.panel_index;
  if (typeof raw === "number" && Number.isFinite(raw)) return raw;
  if (typeof raw === "string" && raw.trim()) {
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export function timelineClipStoryboardSheetUrl(item: TimelineItem | null) {
  const meta = timelineItemMeta(item);
  const sheetRef = asRecord(meta.clip_storyboard_sheet_asset_ref);
  return (
    getString(sheetRef?.file_url) ??
    getString(sheetRef?.url) ??
    getString(sheetRef?.image_url) ??
    getString(sheetRef?.file_path) ??
    getString(meta.image_url) ??
    getString(meta.start_image_url) ??
    getString(meta.end_image_url) ??
    null
  );
}

export function timelineClipHasShotPlan(item: TimelineItem | null) {
  const meta = timelineItemMeta(item);
  const sourceRefs = asRecord(meta.source_refs);
  return Boolean(asRecord(sourceRefs?.timeline_shot_plan));
}

export function timelineClipStartEndFrameStatus(item: TimelineItem | null) {
  const meta = timelineItemMeta(item);
  const startReady =
    hasAssetLocator(meta.start_frame_asset_ref) ||
    Boolean(getString(meta.start_frame_url));
  const endReady =
    hasAssetLocator(meta.end_frame_asset_ref) ||
    Boolean(getString(meta.end_frame_url));
  if (startReady && endReady) {
    return { startReady, endReady, label: "首尾帧已生成" };
  }
  if (startReady) return { startReady, endReady, label: "已有首帧" };
  if (endReady) return { startReady, endReady, label: "已有尾帧" };
  return { startReady, endReady, label: "首尾帧待生成" };
}

export function hasTimelineClipReferenceImages({
  manualReferenceImages,
  characterReferenceImages,
  environmentReferenceImages,
}: {
  manualReferenceImages: string[];
  characterReferenceImages: string[];
  environmentReferenceImages: string[];
}) {
  return (
    manualReferenceImages.length > 0 ||
    characterReferenceImages.length > 0 ||
    environmentReferenceImages.length > 0
  );
}

export function parseOptionalNumber(value: string) {
  if (!value.trim()) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

export function parseReferenceImagesInput(value: string) {
  return dedupeReferenceImages(value.split(/\s+/));
}

function dedupeReferenceImages(
  values?: Array<string | null | undefined> | null,
) {
  const deduped: string[] = [];
  for (const value of values || []) {
    const cleaned = value?.trim();
    if (!cleaned || deduped.includes(cleaned)) continue;
    deduped.push(cleaned);
  }
  return deduped;
}

function hasAssetLocator(value: unknown) {
  if (typeof value === "string" && value.trim()) return true;
  const record = asRecord(value);
  return Boolean(
    getString(record?.file_url) ||
      getString(record?.url) ||
      getString(record?.image_url) ||
      getString(record?.file_path) ||
      typeof record?.media_asset_id === "number" ||
      getString(record?.media_asset_id),
  );
}
