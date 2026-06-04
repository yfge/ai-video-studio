import { asRecord, getString, parseMs } from "@/hooks/episodeDetailUtils";
import type { NormalizedScene, TimelineResponse } from "@/utils/api/types";
import {
  parseShotPlanPromptLayers,
  type ShotPlanPromptLayers,
} from "./WorkspaceStoryboardPromptLayers";

export type StoryboardSupportFrame = {
  id: string;
  frameNumber: number;
  clipId: string | null;
  sceneNumber: string | null;
  sceneLabel: string | null;
  timeLabel: string;
  description: string;
  beatType: string | null;
  speakerName: string | null;
  status: string;
  promptDescription: string | null;
  aiPrompt: string | null;
  imageUrl: string | null;
  videoUrl: string | null;
  sourceKind: string | null;
  gridPanelIndex: number | null;
  promptLayers: ShotPlanPromptLayers | null;
};

export type StoryboardSupportSummary = {
  frameCount: number;
  imageCount: number;
  videoCount: number;
  generationSource: string | null;
  timelineId: string | null;
  timelineVersion: string | null;
  gridSheetUrl: string | null;
  gridPanelCount: number;
  gridGeneratedAt: string | null;
};

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

export type StoryboardGridPanel = {
  panelId: string | null;
  panelIndex: number | null;
  clipId: string | null;
  timeLabel: string;
  visualPrompt: string | null;
  videoPrompt: string | null;
  promptLayers: ShotPlanPromptLayers | null;
};

export type StoryboardGridSupport = {
  sheetUrl: string | null;
  panelCount: number;
  columns: number | null;
  rows: number | null;
  generatedAt: string | null;
  panels: StoryboardGridPanel[];
};

export function buildStoryboardSupportSummary(
  storyboard: Record<string, unknown> | null,
  selectedTimelineSpec?: TimelineResponse | null,
): StoryboardSupportSummary {
  const frames = storyboardFrames(storyboard);
  const meta = asRecord(storyboard?.meta);
  const grid = buildStoryboardGridSupport(selectedTimelineSpec);
  const timeline = selectedTimelineSpec ?? null;
  return {
    frameCount: frames.length,
    imageCount: frames.filter((frame) => Boolean(mediaUrl(frame, IMAGE_KEYS)))
      .length,
    videoCount: frames.filter((frame) => Boolean(mediaUrl(frame, VIDEO_KEYS)))
      .length,
    generationSource: getString(meta?.generation_source) ?? null,
    timelineId: stringify(meta?.timeline_id) ?? stringify(timeline?.id),
    timelineVersion:
      stringify(meta?.timeline_version) ?? stringify(timeline?.version),
    gridSheetUrl: grid.sheetUrl,
    gridPanelCount: grid.panelCount,
    gridGeneratedAt: grid.generatedAt,
  };
}

export function buildStoryboardTimelineOverview(
  selectedTimelineSpec?: TimelineResponse | null,
  selectedAudioTimeline?: Record<string, unknown> | null,
): StoryboardTimelineOverview | null {
  if (!selectedTimelineSpec) return null;
  const spec = selectedTimelineSpec.spec;
  const tracks = Array.isArray(spec?.tracks) ? spec.tracks : [];
  const clipCount = tracks.reduce(
    (total, track) => total + (Array.isArray(track.clips) ? track.clips.length : 0),
    0,
  );
  const dialogueClipCount = countTrackClips(tracks, "dialogue");
  const videoClipCount = countTrackClips(tracks, "video");
  const durationMs =
    numberValue(spec?.duration_ms) ??
    audioDurationMs(spec?.source) ??
    audioDurationMs(selectedAudioTimeline) ??
    maxTrackEndMs(tracks);
  const audio = resolveTimelineAudioSource(spec?.source, selectedAudioTimeline);

  return {
    timelineLabel: `Timeline ${selectedTimelineSpec.id} · v${selectedTimelineSpec.version}`,
    status: getString(selectedTimelineSpec.status) ?? null,
    durationLabel: durationMs != null ? formatDurationMs(durationMs) : "未定时",
    trackSummary: `${tracks.length} 轨 · ${clipCount} clips`,
    trackCount: tracks.length,
    clipCount,
    dialogueClipCount,
    videoClipCount,
    audioUrl: audio.url,
    audioVersion:
      stringify(selectedTimelineSpec.source_audio_timeline_version) ??
      stringify(audio.record?.version),
    audioGeneratedAt: getString(audio.record?.generated_at) ?? null,
  };
}

export function buildStoryboardSupportFrames(
  storyboard: Record<string, unknown> | null,
  normalizedScenes: NormalizedScene[],
  selectedTimelineSpec?: TimelineResponse | null,
): StoryboardSupportFrame[] {
  const scenesByNumber = new Map<string, NormalizedScene>();
  normalizedScenes.forEach((scene) => {
    if (scene.scene_number)
      scenesByNumber.set(String(scene.scene_number), scene);
  });
  const gridPanelsByClipId = new Map<string, StoryboardGridPanel>();
  buildStoryboardGridSupport(selectedTimelineSpec).panels.forEach((panel) => {
    if (panel.clipId) gridPanelsByClipId.set(panel.clipId, panel);
  });

  return storyboardFrames(storyboard).map((frame, index) => {
    const sceneNumber = stringify(frame.scene_number);
    const scene = sceneNumber ? scenesByNumber.get(sceneNumber) : undefined;
    const startMs = parseMs(frame.start_ms);
    const endMs = parseMs(frame.end_ms);
    return {
      id:
        getString(frame.frame_id) ??
        getString(frame.id) ??
        getString(frame.timeline_clip_id) ??
        `frame-${index + 1}`,
      frameNumber: numberValue(frame.frame_number) ?? index + 1,
      clipId: getString(frame.timeline_clip_id) ?? null,
      sceneNumber,
      sceneLabel: scene
        ? [scene.scene_number, scene.slug_line].filter(Boolean).join(" · ")
        : null,
      timeLabel: timeLabel(startMs, endMs, frame.duration_seconds),
      description:
        getString(frame.description) ??
        getString(frame.beat_text) ??
        `分镜 ${index + 1}`,
      beatType: getString(frame.beat_type) ?? null,
      speakerName: getString(frame.speaker_name) ?? null,
      status: getString(frame.status) ?? "draft",
      promptDescription: getString(frame.prompt_description) ?? null,
      aiPrompt: getString(frame.ai_prompt) ?? null,
      imageUrl: mediaUrl(frame, IMAGE_KEYS),
      videoUrl: mediaUrl(frame, VIDEO_KEYS),
      sourceKind: getString(asRecord(frame.source)?.kind) ?? null,
      gridPanelIndex:
        gridPanelsByClipId.get(getString(frame.timeline_clip_id) ?? "")
          ?.panelIndex ?? null,
      promptLayers: parseShotPlanPromptLayers(
        asRecord(frame.shot_plan_prompt_layers) ?? frame,
      ),
    };
  });
}

export function buildStoryboardGridSupport(
  selectedTimelineSpec?: TimelineResponse | null,
): StoryboardGridSupport {
  const supportViews = asRecord(selectedTimelineSpec?.spec?.support_views);
  const grid = asRecord(supportViews?.storyboard_grid);
  const sheet = asRecord(grid?.sheet);
  const panels = Array.isArray(grid?.panels) ? grid.panels : [];
  return {
    sheetUrl: getString(sheet?.file_url) ?? getString(sheet?.file_path) ?? null,
    panelCount: numberValue(sheet?.panel_count) ?? panels.length,
    columns: numberValue(sheet?.columns),
    rows: numberValue(sheet?.rows),
    generatedAt: getString(grid?.generated_at) ?? null,
    panels: panels
      .map((panel) => asRecord(panel))
      .filter((panel): panel is Record<string, unknown> => Boolean(panel))
      .map((panel) => {
        const startMs = parseMs(panel.start_ms);
        const endMs = parseMs(panel.end_ms);
        return {
          panelId: getString(panel.panel_id) ?? null,
          panelIndex: numberValue(panel.panel_index),
          clipId: getString(panel.clip_id) ?? null,
          timeLabel: timeLabel(startMs, endMs, panel.duration_ms),
          visualPrompt: getString(panel.visual_prompt) ?? null,
          videoPrompt: getString(panel.video_prompt) ?? null,
          promptLayers: parseShotPlanPromptLayers(panel),
        };
      }),
  };
}

const IMAGE_KEYS = [
  "image_url",
  "start_image_url",
  "end_image_url",
  "thumbnail_url",
  "keyframe_url",
];

const VIDEO_KEYS = ["video_url", "video_oss_url", "result_video_url"];

function storyboardFrames(
  storyboard: Record<string, unknown> | null,
): Record<string, unknown>[] {
  const frames = Array.isArray(storyboard?.frames) ? storyboard.frames : [];
  return frames
    .map((frame) => asRecord(frame))
    .filter((frame): frame is Record<string, unknown> => Boolean(frame));
}

function mediaUrl(
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

function countTrackClips(
  tracks: TimelineResponse["spec"]["tracks"],
  trackType: string,
): number {
  return tracks
    .filter((track) => track.track_type === trackType)
    .reduce(
      (total, track) => total + (Array.isArray(track.clips) ? track.clips.length : 0),
      0,
    );
}

function maxTrackEndMs(tracks: TimelineResponse["spec"]["tracks"]): number | null {
  const values = tracks.flatMap((track) =>
    Array.isArray(track.clips)
      ? track.clips
          .map((clip) => numberValue(clip.end_ms))
          .filter((value): value is number => value != null)
      : [],
  );
  return values.length ? Math.max(...values) : null;
}

function audioDurationMs(source: unknown): number | null {
  const episodeAudio = timelineEpisodeAudio(source);
  const durationSeconds = numberValue(episodeAudio?.duration_seconds);
  if (durationSeconds != null) return Math.round(durationSeconds * 1000);
  return numberValue(episodeAudio?.duration_ms);
}

function resolveTimelineAudioSource(
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

function timeLabel(
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

function stringify(value: unknown): string | null {
  if (typeof value === "string" && value.trim()) return value;
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  return null;
}

function numberValue(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}
