import { asRecord, getString, parseMs } from "@/hooks/episodeDetailUtils";
import type { NormalizedScene, TimelineResponse } from "@/utils/api/types";
import {
  parseShotPlanPromptLayers,
  type ShotPlanPromptLayers,
} from "./WorkspaceStoryboardPromptLayers";
import {
  IMAGE_KEYS,
  VIDEO_KEYS,
  audioDurationMs,
  countTrackClips,
  formatDurationMs,
  maxTrackEndMs,
  mediaUrl,
  numberValue,
  resolveTimelineAudioSource,
  storyboardFrames,
  stringify,
  timeLabel,
} from "./WorkspaceStoryboardSupportUtils";

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

type StoryboardGridPanel = {
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
    (total, track) =>
      total + (Array.isArray(track.clips) ? track.clips.length : 0),
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
