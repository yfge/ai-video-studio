import { asRecord, getString, parseMs } from "@/hooks/episodeDetailUtils";
import type { TimelineResponse } from "@/utils/api/types";
import {
  audioDurationMs,
  countTrackClips,
  formatDurationMs,
  maxTrackEndMs,
  numberValue,
  resolveTimelineAudioSource,
  stringify,
} from "./WorkspaceStoryboardSupportUtils";

export type StoryboardTimelineOverview = {
  timelineLabel: string;
  status: string | null;
  durationLabel: string;
  trackSummary: string;
  trackCount: number;
  clipCount: number;
  dialogueClipCount: number;
  videoClipCount: number;
  audioUrl: string | null;
  audioVersion: string | null;
  audioGeneratedAt: string | null;
};

export function buildStoryboardTimelineOverview(
  selectedTimelineSpec?: TimelineResponse | null,
  selectedAudioTimeline?: Record<string, unknown> | null,
): StoryboardTimelineOverview {
  const audio = resolveTimelineAudioSource(
    selectedTimelineSpec?.spec?.source,
    selectedAudioTimeline,
  );
  if (!selectedTimelineSpec) {
    const beats: unknown[] = Array.isArray(selectedAudioTimeline?.beats)
      ? selectedAudioTimeline.beats
      : [];
    const durationMs: number | null =
      audioDurationMs(selectedAudioTimeline) ?? maxBeatEndMs(beats);
    return {
      timelineLabel: beats.length ? "音频时间轴" : "Timeline 待生成",
      status: null,
      durationLabel:
        durationMs != null ? formatDurationMs(durationMs) : "未定时",
      trackSummary: `${beats.length ? 1 : 0} 轨 · ${beats.length} clips`,
      trackCount: beats.length ? 1 : 0,
      clipCount: beats.length,
      dialogueClipCount: beats.length,
      videoClipCount: 0,
      audioUrl: audio.url,
      audioVersion: stringify(audio.record?.version),
      audioGeneratedAt: getString(audio.record?.generated_at) ?? null,
    };
  }

  const spec = selectedTimelineSpec.spec;
  const tracks = Array.isArray(spec?.tracks) ? spec.tracks : [];
  const clipCount = tracks.reduce(
    (total, track) =>
      total + (Array.isArray(track.clips) ? track.clips.length : 0),
    0,
  );
  const durationMs =
    numberValue(spec?.duration_ms) ??
    audioDurationMs(spec?.source) ??
    audioDurationMs(selectedAudioTimeline) ??
    maxTrackEndMs(tracks);

  return {
    timelineLabel: `Timeline ${selectedTimelineSpec.id} · v${selectedTimelineSpec.version}`,
    status: getString(selectedTimelineSpec.status) ?? null,
    durationLabel: durationMs != null ? formatDurationMs(durationMs) : "未定时",
    trackSummary: `${tracks.length} 轨 · ${clipCount} clips`,
    trackCount: tracks.length,
    clipCount,
    dialogueClipCount: countTrackClips(tracks, "dialogue"),
    videoClipCount: countTrackClips(tracks, "video"),
    audioUrl: audio.url,
    audioVersion:
      stringify(selectedTimelineSpec.source_audio_timeline_version) ??
      stringify(audio.record?.version),
    audioGeneratedAt: getString(audio.record?.generated_at) ?? null,
  };
}

function maxBeatEndMs(beats: unknown[]): number | null {
  const maxEnd = beats.reduce<number>((currentMax, raw) => {
    const beat = asRecord(raw);
    if (!beat) return currentMax;
    const end: number | null = parseMs(beat.end_ms) ?? parseMs(beat.start_ms);
    return end == null ? currentMax : Math.max(currentMax, end);
  }, Number.NEGATIVE_INFINITY);
  return Number.isFinite(maxEnd) ? maxEnd : null;
}
