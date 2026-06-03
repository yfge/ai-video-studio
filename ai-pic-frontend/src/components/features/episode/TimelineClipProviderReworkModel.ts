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
  useStoryboardGrid,
}: {
  expectedVersion: number;
  action: TimelineClipVideoReworkAction;
  prompt?: string | null;
  model?: string | null;
  duration?: number | null;
  resolution?: string | null;
  ratio?: string | null;
  reason?: string | null;
  useStoryboardGrid?: boolean;
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
  if (useStoryboardGrid) {
    payload.reference_mode = "storyboard_grid_panel";
    payload.use_storyboard_grid = true;
    payload.use_end_frame = false;
  }
  return payload;
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
