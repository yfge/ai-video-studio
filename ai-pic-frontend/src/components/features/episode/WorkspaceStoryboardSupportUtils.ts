import { asRecord, getString } from "@/hooks/episodeDetailUtils";
import type { TimelineResponse } from "@/utils/api/types";

export const IMAGE_KEYS = [
  "image_url",
  "start_image_url",
  "end_image_url",
  "thumbnail_url",
  "keyframe_url",
];

export const VIDEO_KEYS = ["video_url", "video_oss_url", "result_video_url"];

export function storyboardFrames(
  storyboard: Record<string, unknown> | null,
): Record<string, unknown>[] {
  const frames = Array.isArray(storyboard?.frames) ? storyboard.frames : [];
  return frames
    .map((frame) => asRecord(frame))
    .filter((frame): frame is Record<string, unknown> => Boolean(frame));
}

export function mediaUrl(
  record: Record<string, unknown>,
  keys: string[],
): string | null {
  for (const key of keys) {
    const value = getString(record[key]);
    if (value) return value;
  }
  for (const key of [
    "image_urls",
    "start_image_urls",
    "end_image_urls",
    "video_urls",
  ]) {
    const values = Array.isArray(record[key]) ? record[key] : [];
    const first = values.map((value) => getString(value)).find(Boolean);
    if (first) return first;
  }
  return null;
}

export function countTrackClips(
  tracks: TimelineResponse["spec"]["tracks"],
  trackType: string,
): number {
  return tracks
    .filter((track) => track.track_type === trackType)
    .reduce(
      (total, track) =>
        total + (Array.isArray(track.clips) ? track.clips.length : 0),
      0,
    );
}

export function maxTrackEndMs(
  tracks: TimelineResponse["spec"]["tracks"],
): number | null {
  const values = tracks.flatMap((track) =>
    Array.isArray(track.clips)
      ? track.clips
          .map((clip) => numberValue(clip.end_ms))
          .filter((value): value is number => value != null)
      : [],
  );
  return values.length ? Math.max(...values) : null;
}

export function audioDurationMs(source: unknown): number | null {
  const episodeAudio = timelineEpisodeAudio(source);
  const durationSeconds = numberValue(episodeAudio?.duration_seconds);
  if (durationSeconds != null) return Math.round(durationSeconds * 1000);
  return numberValue(episodeAudio?.duration_ms);
}

export function resolveTimelineAudioSource(
  timelineSource: unknown,
  selectedAudioTimeline?: Record<string, unknown> | null,
): { url: string | null; record: Record<string, unknown> | null } {
  const candidates = [
    timelineEpisodeAudio(timelineSource),
    timelineEpisodeAudio(selectedAudioTimeline),
    asRecord(selectedAudioTimeline),
  ];
  for (const record of candidates) {
    const url = audioUrl(record);
    if (url) return { url, record };
  }
  return { url: null, record: candidates.find(Boolean) ?? null };
}

function timelineEpisodeAudio(source: unknown): Record<string, unknown> | null {
  const record = asRecord(source);
  return asRecord(record?.episode_audio);
}

function audioUrl(record: Record<string, unknown> | null): string | null {
  if (!record) return null;
  for (const key of ["oss_url", "audio_url", "file_url", "url", "file_path"]) {
    const value = getString(record[key]);
    if (value) return value;
  }
  return null;
}

export function timeLabel(
  startMs: number | null,
  endMs: number | null,
  durationSeconds: unknown,
): string {
  if (startMs !== null && endMs !== null) {
    return `${formatMs(startMs)} - ${formatMs(endMs)}`;
  }
  const duration = numberValue(durationSeconds);
  return duration ? `${duration.toFixed(1)}s` : "未定时";
}

function formatDurationMs(value: number): string {
  if (value < 60_000) return `${(value / 1000).toFixed(1)}s`;
  const totalSeconds = Math.round(value / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

function formatMs(value: number): string {
  const seconds = Math.floor(value / 1000);
  const ms = value % 1000;
  const minutes = Math.floor(seconds / 60);
  const rem = seconds % 60;
  return `${minutes}:${String(rem).padStart(2, "0")}.${String(ms).padStart(
    3,
    "0",
  )}`;
}

export function stringify(value: unknown): string | null {
  if (typeof value === "string" && value.trim()) return value;
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  return null;
}

export function numberValue(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export { formatDurationMs };
