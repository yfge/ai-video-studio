"use client";

import { asRecord, getString, parseMs } from "@/hooks/useEpisodeDetail";
import type { TimelineClip, TimelineResponse } from "@/utils/api/types";

export type MissingTimelineClip = {
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

export function buildTimelineRenderReadiness(
  selectedTimelineSpec: TimelineResponse | null,
  selectedStoryboard: Record<string, unknown> | null,
): TimelineRenderReadiness {
  const clips = timelineVideoClips(selectedTimelineSpec);
  const missingClips = clips
    .filter((clip) => !timelineClipVideoStatus(clip, selectedStoryboard).ready)
    .map((clip) => ({
      clipId: getString(clip.clip_id) || getString(clip.id) || "unknown",
      sceneNumber:
        getString(clip.scene_number) ||
        getString(clip.scene) ||
        getString(clip.scene_id) ||
        null,
      startMs: parseMs(clip.start_ms),
      endMs: parseMs(clip.end_ms),
      reason: "missing_video_url",
    }));

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
  for (const key of ["video_url", "video_oss_url", "result_video_url", "file_url"]) {
    const value = getString(record[key]);
    if (value) return value;
  }

  const assetRef = asRecord(record.asset_ref);
  if (assetRef) {
    for (const key of ["file_url", "url", "video_url", "video_oss_url", "file_path"]) {
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
