"use client";
import type { TimelineItem, TimelineTrack } from "@/components/features";
import { asRecord, getString, parseMs } from "@/hooks/useEpisodeDetail";
import type { TimelineResponse, TimelineTrackSpec } from "@/utils/api/types";
import {
  audioTimelineBeatContextById,
  enrichTimelineClipMetaFromAudioBeat,
} from "./EpisodeTimelineAudioBeatEnrichment";
export { sceneForTimelineMeta } from "./EpisodeTimelineSceneModel";
export const formatTimelineMs = (ms: number) => {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`;
};

export const timelineItemMeta = (item: TimelineItem | null) =>
  asRecord(item?.meta) ?? {};

const hasVideoAsset = (record: Record<string, unknown>) =>
  Boolean(
    getString(record.video_url) ||
      getString(record.video_oss_url) ||
      getString(record.result_video_url) ||
      (Array.isArray(record.video_urls) && record.video_urls.length > 0),
  );

export function buildEpisodeTimelineTracks(
  selectedTimelineSpec: TimelineResponse | null,
  selectedAudioTimeline: Record<string, unknown> | null,
  selectedStoryboard: Record<string, unknown> | null,
): TimelineTrack[] {
  const nativeTracks = timelineSpecToTimelineTracks(
    selectedTimelineSpec,
    selectedAudioTimeline,
    selectedStoryboard,
  );
  if (nativeTracks.length > 0) return nativeTracks;
  return legacyAudioTimelineToTimelineTracks(
    selectedAudioTimeline,
    selectedStoryboard,
  );
}

function legacyAudioTimelineToTimelineTracks(
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
        displayLabel: timelineItemDisplayLabel("dialogue", idx),
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
        displayLabel: timelineItemDisplayLabel("storyboard", idx),
        type: "storyboard",
        color: "#7c3aed",
        meta: record,
      };
    })
    .filter((item): item is TimelineItem => Boolean(item));

  const videoItems = frameItems
    .filter((item) => hasVideoAsset(timelineItemMeta(item)))
    .map<TimelineItem>((item, idx) => ({
      ...item,
      id: `video-${item.id}`,
      label: item.label ? `视频 ${item.label}` : "视频片段",
      displayLabel: timelineItemDisplayLabel("video", idx),
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
  return prioritizeTimelineTracks(
    tracks.filter((track): track is TimelineTrack => Boolean(track)),
  );
}

function timelineSpecToTimelineTracks(
  selectedTimelineSpec: TimelineResponse | null,
  selectedAudioTimeline: Record<string, unknown> | null,
  selectedStoryboard: Record<string, unknown> | null,
): TimelineTrack[] {
  const specTracks = Array.isArray(selectedTimelineSpec?.spec?.tracks)
    ? selectedTimelineSpec.spec.tracks
    : [];
  const audioBeatById = audioTimelineBeatContextById(selectedAudioTimeline);
  const timelineTracks = specTracks
    .map((track) => timelineSpecTrackToTimelineTrack(track, audioBeatById))
    .filter((track): track is TimelineTrack => Boolean(track));

  const storyboardTrack = storyboardSupportTrack(selectedStoryboard);
  const tracks = storyboardTrack
    ? [...timelineTracks, storyboardTrack]
    : timelineTracks;
  return prioritizeTimelineTracks(tracks);
}

function timelineSpecTrackToTimelineTrack(
  track: TimelineTrackSpec,
  audioBeatById: Map<string, Record<string, unknown>>,
): TimelineTrack | null {
  const trackType = track.track_type || String(track.type || "");
  const clips = Array.isArray(track.clips) ? track.clips : [];
  const items = clips
    .map<TimelineItem | null>((clip, idx) => {
      const start = parseMs(clip.start_ms);
      const end = parseMs(clip.end_ms);
      if (start == null || end == null || end < start) return null;
      const meta = enrichTimelineClipMetaFromAudioBeat(clip, audioBeatById);
      const label =
        getString(meta.text) ||
        getString(meta.speaker_name) ||
        `${timelineTrackLabel(trackType)} ${idx + 1}`;
      return {
        id: `${trackType}-${clip.clip_id || idx}`,
        startMs: start,
        endMs: end,
        label,
        displayLabel: timelineItemDisplayLabel(trackType, idx),
        type: trackType || "clip",
        color: timelineTrackColor(trackType),
        meta,
      };
    })
    .filter((item): item is TimelineItem => Boolean(item));
  if (!items.length) return null;
  return {
    id: trackType || "timeline",
    label: timelineTrackLabel(trackType),
    color: timelineTrackColor(trackType),
    items,
  };
}

function storyboardSupportTrack(
  selectedStoryboard: Record<string, unknown> | null,
): TimelineTrack | null {
  const frames = Array.isArray(selectedStoryboard?.frames)
    ? (selectedStoryboard?.frames as unknown[])
    : [];
  const items = frames
    .map<TimelineItem | null>((raw, idx) => {
      const record = asRecord(raw);
      const start = parseMs(record?.start_ms);
      const end = parseMs(record?.end_ms);
      if (!record || start == null || end == null || end < start) return null;
      const id =
        getString(record.frame_id) ||
        getString(record.timeline_clip_id) ||
        getString(record.id) ||
        String(idx);
      return {
        id: `storyboard-${id}`,
        startMs: start,
        endMs: end,
        label: getString(record.description) || `分镜 ${idx + 1}`,
        displayLabel: timelineItemDisplayLabel("storyboard", idx),
        type: "storyboard",
        color: "#7c3aed",
        meta: record,
      };
    })
    .filter((item): item is TimelineItem => Boolean(item));
  return items.length
    ? { id: "storyboard", label: "分镜", color: "#7c3aed", items }
    : null;
}

function timelineTrackLabel(trackType: string) {
  if (trackType === "dialogue") return "对白";
  if (trackType === "video") return "视频";
  if (trackType === "subtitle") return "字幕";
  return trackType || "时间轴";
}

function timelineItemDisplayLabel(trackType: string, index: number) {
  if (trackType === "dialogue") return `对白 ${index + 1}`;
  if (trackType === "video") return `视频 ${index + 1}`;
  if (trackType === "subtitle") return `字幕 ${index + 1}`;
  if (trackType === "storyboard") return `分镜 ${index + 1}`;
  return undefined;
}

function timelineTrackColor(trackType: string) {
  if (trackType === "dialogue") return "#2563eb";
  if (trackType === "video") return "#0f766e";
  if (trackType === "subtitle") return "#d97706";
  return "#475569";
}

function prioritizeTimelineTracks(tracks: TimelineTrack[]) {
  const priority = (track: TimelineTrack) => {
    if (track.id === "video") return 0;
    if (track.id === "dialogue") return 1;
    if (track.id === "subtitle") return 2;
    if (track.id === "storyboard") return 3;
    return 4;
  };
  return [...tracks].sort((a, b) => priority(a) - priority(b));
}
