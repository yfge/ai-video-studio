import { asRecord, getString, parseMs } from "@/hooks/episodeDetailUtils";
import type {
  NormalizedScene,
  TimelineClip,
  TimelineResponse,
} from "@/utils/api/types";
import {
  clipContextStatus,
  clipKeyframeStatus,
  hasClipStoryboardReference,
  hasClipVideo,
  sceneForStoryboardClip,
} from "./WorkspaceStoryboardClipManagementStatus";
import { timeLabel } from "./WorkspaceStoryboardSupportUtils";

export type StoryboardClipManagementItem = {
  clipId: string;
  label: string;
  timeLabel: string;
  sceneLabel: string | null;
  contextStatusLabel: string;
  contextStatusReady: boolean;
  storyboardStatusLabel: string;
  storyboardReady: boolean;
  keyframeStatusLabel: string;
  keyframeReady: boolean;
  videoStatusLabel: string;
  videoReady: boolean;
};

export function buildStoryboardClipManagementItems(
  selectedTimelineSpec: TimelineResponse | null,
  selectedStoryboard: Record<string, unknown> | null,
  normalizedScenes: NormalizedScene[] = [],
): StoryboardClipManagementItem[] {
  const clipStoryboards = timelineClipStoryboards(selectedTimelineSpec);
  return timelineVideoClips(selectedTimelineSpec).map((clip, index) => {
    const clipId = getString(clip.clip_id) || getString(clip.id) || "";
    const scene = sceneForStoryboardClip(clip, normalizedScenes);
    const context = clipContextStatus(clip, scene);
    const storyboardReady = hasClipStoryboardReference(
      clip,
      clipStoryboards.get(clipId),
    );
    const keyframes = clipKeyframeStatus(clip, selectedStoryboard);
    const videoReady = hasClipVideo(clip, selectedStoryboard);

    return {
      clipId,
      label: clipLabel(clip, index),
      timeLabel: timeLabel(parseMs(clip.start_ms), parseMs(clip.end_ms), null),
      sceneLabel: scene ? `${scene.scene_number} · ${scene.slug_line}` : null,
      contextStatusLabel: context.label,
      contextStatusReady: context.ready,
      storyboardStatusLabel: storyboardReady ? "故事板已生成" : "故事板待生成",
      storyboardReady,
      keyframeStatusLabel: keyframes.label,
      keyframeReady: keyframes.ready,
      videoStatusLabel: videoReady ? "视频已生成" : "视频待生成",
      videoReady,
    };
  });
}

function timelineVideoClips(
  selectedTimelineSpec: TimelineResponse | null,
): TimelineClip[] {
  const tracks = Array.isArray(selectedTimelineSpec?.spec?.tracks)
    ? selectedTimelineSpec.spec.tracks
    : [];
  return tracks
    .filter((track) => (track.track_type || track.type) === "video")
    .flatMap((track) => (Array.isArray(track.clips) ? track.clips : []))
    .filter((clip) => Boolean(getString(clip.clip_id) || getString(clip.id)));
}

function timelineClipStoryboards(
  selectedTimelineSpec: TimelineResponse | null,
) {
  const supportViews = asRecord(selectedTimelineSpec?.spec?.support_views);
  const clipStoryboards = asRecord(supportViews?.clip_storyboards);
  const result = new Map<string, Record<string, unknown>>();
  if (!clipStoryboards) return result;
  Object.entries(clipStoryboards).forEach(([clipId, value]) => {
    const record = asRecord(value);
    if (clipId && record) result.set(clipId, record);
  });
  return result;
}

function clipLabel(clip: TimelineClip, index: number) {
  return (
    getString(clip.text) ||
    getString(clip.speaker_name) ||
    getString(asRecord(clip.source_refs)?.plot) ||
    `视频 ${index + 1}`
  );
}
