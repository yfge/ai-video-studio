import { asRecord, getString } from "@/hooks/episodeDetailUtils";
import type { TimelineResponse, TimelineSpec } from "@/utils/api/types";

export type ShotPlanMotionPoint = {
  atMs: number;
  action: string;
};

export type ShotPlanPromptLayers = {
  directionAnchor: string;
  aestheticReference: string;
  shotType: string;
  cameraMovement: string;
  compositionGeometry: string;
  motionTimeline: ShotPlanMotionPoint[];
  emotionalLanding: string;
  promptMethod: string;
};

export function buildShotPlanPromptLayerPatch(
  timeline: TimelineResponse,
  clipId: string,
  layers: ShotPlanPromptLayers,
): TimelineSpec | null {
  const spec = cloneTimelineSpec(timeline.spec);
  let patched = false;

  spec.tracks = spec.tracks.map((track) => {
    if (track.track_type !== "video") return track;
    return {
      ...track,
      clips: track.clips.map((clip) => {
        const sourceRefs = asRecord(clip.source_refs) ?? {};
        const nextSourceRefs = { ...sourceRefs };
        delete nextSourceRefs.grid_storyboard_panel;

        if (clip.clip_id !== clipId) {
          return { ...clip, source_refs: nextSourceRefs };
        }

        patched = true;
        const existingShotPlan =
          asRecord(nextSourceRefs.timeline_shot_plan) ?? {};
        nextSourceRefs.timeline_shot_plan = {
          ...existingShotPlan,
          ...shotPlanPromptLayersToApi(layers),
          clip_id: clip.clip_id,
          duration_ms: clip.duration_ms ?? clip.end_ms - clip.start_ms,
        };
        return { ...clip, source_refs: nextSourceRefs };
      }),
    };
  });

  if (!patched) return null;

  const supportViews = asRecord(spec.support_views);
  if (supportViews) {
    const nextSupportViews = { ...supportViews };
    delete nextSupportViews.storyboard_grid;
    spec.support_views = nextSupportViews;
  }
  return spec;
}

export function parseShotPlanPromptLayers(
  record: Record<string, unknown> | null | undefined,
): ShotPlanPromptLayers | null {
  if (!record) return null;
  const directionAnchor = getString(record.direction_anchor) ?? "";
  const aestheticReference = getString(record.aesthetic_reference) ?? "";
  const shotType = getString(record.shot_type) ?? "";
  const cameraMovement = getString(record.camera_movement) ?? "";
  const compositionGeometry = getString(record.composition_geometry) ?? "";
  const emotionalLanding = getString(record.emotional_landing) ?? "";
  const promptMethod =
    getString(record.prompt_method) ??
    "direction_reference_geometry_timeline_emotion_v1";
  const motionTimeline = parseMotionTimeline(record.motion_timeline);

  if (
    !directionAnchor &&
    !aestheticReference &&
    !shotType &&
    !cameraMovement &&
    !compositionGeometry &&
    motionTimeline.length === 0 &&
    !emotionalLanding
  ) {
    return null;
  }

  return {
    directionAnchor,
    aestheticReference,
    shotType,
    cameraMovement,
    compositionGeometry,
    motionTimeline,
    emotionalLanding,
    promptMethod,
  };
}

export function emptyShotPlanPromptLayers(): ShotPlanPromptLayers {
  return {
    directionAnchor: "",
    aestheticReference: "",
    shotType: "",
    cameraMovement: "",
    compositionGeometry: "",
    motionTimeline: [
      { atMs: 0, action: "" },
      { atMs: 1000, action: "" },
    ],
    emotionalLanding: "",
    promptMethod: "direction_reference_geometry_timeline_emotion_v1",
  };
}

export function motionTimelineLabel(layers: ShotPlanPromptLayers | null): string {
  if (!layers || layers.motionTimeline.length === 0) return "";
  return layers.motionTimeline
    .map((point) => `${point.atMs}ms ${point.action}`)
    .join(" / ");
}

function shotPlanPromptLayersToApi(
  layers: ShotPlanPromptLayers,
): Record<string, unknown> {
  return {
    direction_anchor: layers.directionAnchor.trim(),
    aesthetic_reference: layers.aestheticReference.trim(),
    shot_type: layers.shotType.trim(),
    camera_movement: layers.cameraMovement.trim(),
    composition_geometry: layers.compositionGeometry.trim(),
    motion_timeline: layers.motionTimeline
      .filter((point) => Number.isFinite(point.atMs) && point.action.trim())
      .map((point) => ({ at_ms: point.atMs, action: point.action.trim() })),
    emotional_landing: layers.emotionalLanding.trim(),
    prompt_method:
      layers.promptMethod.trim() ||
      "direction_reference_geometry_timeline_emotion_v1",
  };
}

function cloneTimelineSpec(spec: TimelineSpec): TimelineSpec {
  return JSON.parse(JSON.stringify(spec)) as TimelineSpec;
}

function parseMotionTimeline(value: unknown): ShotPlanMotionPoint[] {
  const points = Array.isArray(value) ? value : [];
  return points
    .map((item) => asRecord(item))
    .filter((item): item is Record<string, unknown> => Boolean(item))
    .map((item) => {
      const atMs = numberValue(item.at_ms);
      const action = getString(item.action);
      if (atMs === null || !action) return null;
      return { atMs, action };
    })
    .filter((item): item is ShotPlanMotionPoint => Boolean(item));
}

function numberValue(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}
