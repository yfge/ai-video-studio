"use client";

import { asRecord, getString, parseMs } from "@/hooks/useEpisodeDetail";
import type {
  TimelineClip,
  TimelineResolvedVideoItem,
  TimelineResolvedVideoListResponse,
  TimelineResponse,
} from "@/utils/api/types";

type MissingTimelineClip = {
  clipId: string;
  sceneNumber?: string | null;
  startMs?: number | null;
  endMs?: number | null;
  reason: string;
};

export type TimelineRenderReadiness = {
  ready: boolean;
  videoClipCount: number;
  missingClips: MissingTimelineClip[];
};

export type TimelineClipVideoStatus = {
  ready: boolean;
  url?: string | null;
  source?: string | null;
  reason?: string | null;
};

export function buildTimelineRenderReadinessFromResolvedVideos(
  resolvedVideos: TimelineResolvedVideoListResponse | null,
): TimelineRenderReadiness {
  if (!resolvedVideos) {
    return { ready: false, videoClipCount: 0, missingClips: [] };
  }
  const missingClips = resolvedVideos.items
    .filter((item) => item.status !== "ready")
    .map((item) => ({
      clipId: item.clip_id,
      sceneNumber:
        getString(item.scene_number) || getString(item.scene_id) || null,
      startMs: parseMs(item.start_ms),
      endMs: parseMs(item.end_ms),
      reason:
        item.status === "generating"
          ? "generating"
          : item.reason || "missing_video_url",
    }));
  return {
    ready: resolvedVideos.ready,
    videoClipCount: resolvedVideos.video_clip_count,
    missingClips,
  };
}

export function resolvedVideoForClipId(
  resolvedVideos: TimelineResolvedVideoListResponse | null,
  clipId?: string | null,
): TimelineResolvedVideoItem | null {
  if (!resolvedVideos || !clipId) return null;
  return resolvedVideos.items.find((item) => item.clip_id === clipId) ?? null;
}

export function timelineClipVideoStatusFromResolvedVideo(
  item: TimelineResolvedVideoItem | null,
): TimelineClipVideoStatus | null {
  if (!item) return null;
  if (item.status === "ready" && item.url) {
    return { ready: true, url: item.url, source: item.source || "resolved" };
  }
  return {
    ready: false,
    reason: item.status === "generating" ? "generating" : item.reason,
    source: item.source,
  };
}

export function buildTimelineRenderReadiness(
  selectedTimelineSpec: TimelineResponse | null,
  selectedStoryboard: Record<string, unknown> | null,
  activeClipTaskIds?: ReadonlySet<string>,
): TimelineRenderReadiness {
  const clips = timelineVideoClips(selectedTimelineSpec);
  const missingClips = clips
    .filter((clip) => !timelineClipVideoStatus(clip, selectedStoryboard).ready)
    .map((clip) => {
      const clipId = getString(clip.clip_id) || getString(clip.id) || "unknown";
      return {
        clipId,
        sceneNumber:
          getString(clip.scene_number) ||
          getString(clip.scene) ||
          getString(clip.scene_id) ||
          null,
        startMs: parseMs(clip.start_ms),
        endMs: parseMs(clip.end_ms),
        reason: activeClipTaskIds?.has(clipId)
          ? "generating"
          : "missing_video_url",
      };
    });

  return {
    ready: clips.length > 0 && missingClips.length === 0,
    videoClipCount: clips.length,
    missingClips,
  };
}

export function timelineClipVideoStatus(
  clipLike: Record<string, unknown> | null,
  selectedStoryboard: Record<string, unknown> | null,
): TimelineClipVideoStatus {
  if (!clipLike) {
    return { ready: false, reason: "missing_clip" };
  }

  const direct = directClipVideoUrl(clipLike);
  if (direct) {
    return { ready: true, url: direct, source: "timeline_clip" };
  }

  const frame = matchingStoryboardFrame(clipLike, selectedStoryboard);
  const frameUrl = frame ? frameVideoUrl(frame) : null;
  if (frameUrl) {
    return { ready: true, url: frameUrl, source: "storyboard_frame" };
  }

  return { ready: false, reason: "missing_video_url" };
}

function timelineVideoClips(
  selectedTimelineSpec: TimelineResponse | null,
): TimelineClip[] {
  const specTracks = Array.isArray(selectedTimelineSpec?.spec?.tracks)
    ? selectedTimelineSpec.spec.tracks
    : [];
  return specTracks
    .filter((track) => track.track_type === "video")
    .flatMap((track) => (Array.isArray(track.clips) ? track.clips : []));
}

function directClipVideoUrl(record: Record<string, unknown>) {
  for (const key of [
    "video_url",
    "video_oss_url",
    "result_video_url",
    "file_url",
  ]) {
    const value = getString(record[key]);
    if (value) return value;
  }

  const assetRef = asRecord(record.asset_ref);
  if (assetRef) {
    for (const key of [
      "file_url",
      "url",
      "video_url",
      "video_oss_url",
      "file_path",
    ]) {
      const value = getString(assetRef[key]);
      if (value) return value;
    }
  }
  return null;
}

function matchingStoryboardFrame(
  record: Record<string, unknown>,
  selectedStoryboard: Record<string, unknown> | null,
) {
  const frames = Array.isArray(selectedStoryboard?.frames)
    ? (selectedStoryboard?.frames as unknown[])
    : [];
  const clipIds = new Set(
    [
      getString(record.clip_id),
      getString(record.id),
      getString(record.frame_id),
      getString(record.storyboard_frame_id),
      getString(asRecord(record.source)?.storyboard_frame_id),
      getString(asRecord(record.source_refs)?.storyboard_frame_id),
    ].filter(Boolean),
  );

  for (const raw of frames) {
    const frame = asRecord(raw);
    if (!frame) continue;
    const frameIds = [
      getString(frame.timeline_clip_id),
      getString(frame.frame_id),
      getString(frame.id),
    ].filter(Boolean);
    if (frameIds.some((value) => clipIds.has(value))) return frame;
  }
  return null;
}

function frameVideoUrl(record: Record<string, unknown>) {
  for (const key of ["video_url", "video_oss_url", "result_video_url"]) {
    const value = getString(record[key]);
    if (value) return value;
  }
  const values = Array.isArray(record.video_urls) ? record.video_urls : [];
  for (const value of values) {
    const url = getString(value);
    if (url) return url;
  }
  return null;
}
