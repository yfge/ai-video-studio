import type { TimelineItem } from "@/components/features";
import { asRecord, getString } from "@/hooks/useEpisodeDetail";
import type {
  TimelineClipVideoReworkAction,
  TimelineClipVideoReworkTaskRequest,
} from "@/utils/api/types";
import { timelineItemMeta } from "./EpisodeTimelineWorkspaceModel";

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
  useClipStoryboard,
}: {
  expectedVersion: number;
  action: TimelineClipVideoReworkAction;
  prompt?: string | null;
  model?: string | null;
  duration?: number | null;
  resolution?: string | null;
  ratio?: string | null;
  reason?: string | null;
  useClipStoryboard?: boolean;
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
  if (useClipStoryboard) {
    payload.reference_mode = "clip_storyboard_panel";
    payload.use_clip_storyboard = true;
    payload.use_end_frame = false;
  }
  return payload;
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
    null
  );
}

export function timelineClipGridPanelIndex(item: TimelineItem | null) {
  const meta = timelineItemMeta(item);
  const sourceRefs = asRecord(meta.source_refs);
  const gridPanel = asRecord(sourceRefs?.grid_storyboard_panel);
  const raw = gridPanel?.panel_index;
  if (typeof raw === "number" && Number.isFinite(raw)) return raw;
  if (typeof raw === "string" && raw.trim()) {
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export function parseOptionalNumber(value: string) {
  if (!value.trim()) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}
