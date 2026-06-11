import { asRecord, getString, parseMs } from "@/hooks/episodeDetailUtils";
import type {
  NormalizedScene,
  TimelineClip,
  TimelineResolvedVideoListResponse,
  TimelineResponse,
} from "@/utils/api/types";
import { resolvedVideoForClipId } from "./EpisodeTimelineRenderModel";
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
  videoUrl: string | null;
};

export function buildStoryboardClipManagementItems(
  selectedTimelineSpec: TimelineResponse | null,
  selectedStoryboard: Record<string, unknown> | null,
  normalizedScenes: NormalizedScene[] = [],
  resolvedVideos?: TimelineResolvedVideoListResponse | null,
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
    const resolvedVideo = resolvedVideoForClipId(resolvedVideos ?? null, clipId);
    const fallbackVideoReady = hasClipVideo(clip, selectedStoryboard);
    const videoReady = resolvedVideo
      ? resolvedVideo.status === "ready" && Boolean(resolvedVideo.url)
      : fallbackVideoReady;
    const videoStatusLabel = resolvedVideo
      ? resolvedVideoStatusLabel(resolvedVideo.status)
      : videoReady
        ? "视频已生成"
        : "视频待生成";

    return {
      clipId,
      label: clipLabel(clip, index),
      timeLabel: timeLabel(parseMs(clip.start_ms), parseMs(clip.end_ms), null),
      sceneLabel: scene ? `${scene.scene_number} · ${scene.slug_line}` : null,
      contextStatusLabel: context.label,
      contextStatusReady: context.ready,
      storyboardStatusLabel: storyboardReady ? "分镜已生成" : "分镜待生成",
      storyboardReady,
      keyframeStatusLabel: keyframes.label,
      keyframeReady: keyframes.ready,
      videoStatusLabel,
      videoReady,
      videoUrl: resolvedVideo?.url || null,
    };
  });
}

function resolvedVideoStatusLabel(status: string) {
  if (status === "ready") return "视频已生成";
  if (status === "generating") return "视频生成中";
  return "视频待生成";
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
