"use client";

import type { TimelineItem, TimelineTrack } from "@/components/features";
import { asRecord, getString, parseMs } from "@/hooks/useEpisodeDetail";

export const formatTimelineMs = (ms: number) => {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`;
};

export const timelineItemMeta = (item: TimelineItem | null) =>
  asRecord(item?.meta) ?? {};

const hasVideoAsset = (record: Record<string, unknown>) => {
  const urls = record.video_urls;
  return Boolean(
    getString(record.video_url) ||
      getString(record.video_oss_url) ||
      getString(record.result_video_url) ||
      (Array.isArray(urls) && urls.length > 0),
  );
};

export function buildEpisodeTimelineTracks(
  selectedAudioTimeline: Record<string, unknown> | null,
  selectedStoryboard: Record<string, unknown> | null,
): TimelineTrack[] {
  const beats = Array.isArray(selectedAudioTimeline?.beats)
    ? (selectedAudioTimeline?.beats as unknown[])
    : [];
  const frames = Array.isArray(selectedStoryboard?.frames)
    ? (selectedStoryboard?.frames as unknown[])
    : [];

  const beatItems = beats
    .map<TimelineItem | null>((raw, idx) => {
      const record = asRecord(raw);
      const start = parseMs(record?.start_ms);
      const end = parseMs(record?.end_ms);
      if (!record || start == null || end == null || end < start) return null;
      const label =
        getString(record.dialogue_excerpt) ||
        getString(record.text) ||
        getString(record.beat_summary) ||
        `Beat ${idx + 1}`;
      return {
        id: `beat-${idx}-${start}`,
        startMs: start,
        endMs: end,
        label,
        type: getString(record.beat_type) || "dialogue",
        color: "#2563eb",
        meta: record,
      };
    })
    .filter((item): item is TimelineItem => Boolean(item));

  const frameItems = frames
    .map<TimelineItem | null>((raw, idx) => {
      const record = asRecord(raw);
      const start = parseMs(record?.start_ms);
      const end = parseMs(record?.end_ms);
      if (!record || start == null || end == null || end < start) return null;
      const id =
        getString(record.frame_id) || getString(record.id) || String(idx);
      return {
        id: `frame-${id}`,
        startMs: start,
        endMs: end,
        label: getString(record.description) || `分镜 ${idx + 1}`,
        type: "storyboard",
        color: "#7c3aed",
        meta: record,
      };
    })
    .filter((item): item is TimelineItem => Boolean(item));

  const videoItems = frameItems
    .filter((item) => hasVideoAsset(timelineItemMeta(item)))
    .map<TimelineItem>((item) => ({
      ...item,
      id: `video-${item.id}`,
      label: item.label ? `视频 ${item.label}` : "视频片段",
      type: "video",
      color: "#0f766e",
    }));

  const tracks: Array<TimelineTrack | null> = [
    beatItems.length
      ? { id: "dialogue", label: "对白", color: "#2563eb", items: beatItems }
      : null,
    frameItems.length
      ? { id: "storyboard", label: "分镜", color: "#7c3aed", items: frameItems }
      : null,
    videoItems.length
      ? { id: "video", label: "视频", color: "#0f766e", items: videoItems }
      : null,
  ];
  return tracks.filter((track): track is TimelineTrack => Boolean(track));
}
