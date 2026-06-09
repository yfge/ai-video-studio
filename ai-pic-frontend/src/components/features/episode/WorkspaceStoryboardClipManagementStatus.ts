import { asRecord, getString } from "@/hooks/episodeDetailUtils";
import type { NormalizedScene, TimelineClip } from "@/utils/api/types";
import {
  IMAGE_KEYS,
  VIDEO_KEYS,
  mediaUrl,
  storyboardFrames,
} from "./WorkspaceStoryboardSupportUtils";

export function sceneForStoryboardClip(
  clip: TimelineClip,
  scenes: NormalizedScene[],
) {
  const sourceRefs = asRecord(clip.source_refs);
  const sceneId = numberLike(clip.scene_id ?? sourceRefs?.scene_id);
  if (sceneId != null) {
    const byId = scenes.find((scene) => scene.id === sceneId);
    if (byId) return byId;
  }
  const sceneNumber =
    getString(clip.scene_number) ||
    getString(clip.scene) ||
    getString(sourceRefs?.scene_number) ||
    getString(sourceRefs?.scene);
  if (!sceneNumber) return null;
  return (
    scenes.find(
      (scene) =>
        String(scene.scene_number) === sceneNumber.replace(/^scene-/i, ""),
    ) ?? null
  );
}

export function clipContextStatus(
  clip: TimelineClip,
  scene: NormalizedScene | null,
) {
  const environmentReady = hasEnvironmentBinding(clip, scene);
  const virtualIpReady = hasVirtualIpBinding(clip);
  return {
    ready: environmentReady && virtualIpReady,
    label: contextStatusLabel(environmentReady, virtualIpReady),
  };
}

export function hasClipStoryboardReference(
  clip: TimelineClip,
  supportViewStoryboard?: Record<string, unknown>,
) {
  const sourceRefs = asRecord(clip.source_refs);
  const supportSheet = asRecord(supportViewStoryboard?.sheet);
  return Boolean(
    hasAssetLocator(asRecord(clip.clip_storyboard_sheet_asset_ref)) ||
      asRecord(sourceRefs?.clip_storyboard) ||
      hasAssetLocator(supportSheet),
  );
}

export function clipKeyframeStatus(
  clip: TimelineClip,
  selectedStoryboard: Record<string, unknown> | null,
) {
  const frame = matchingStoryboardFrame(clip, selectedStoryboard);
  const startReady = Boolean(
    hasAssetLocator(asRecord(clip.start_frame_asset_ref)) ||
      getString(clip.start_frame_url) ||
      getString(frame?.start_image_url),
  );
  const endReady = Boolean(
    hasAssetLocator(asRecord(clip.end_frame_asset_ref)) ||
      getString(clip.end_frame_url) ||
      getString(frame?.end_image_url),
  );
  if (startReady && endReady) return { ready: true, label: "首尾帧已生成" };
  if (startReady) return { ready: false, label: "已有首帧" };
  if (endReady) return { ready: false, label: "已有尾帧" };
  if (frame && mediaUrl(frame, IMAGE_KEYS)) {
    return { ready: false, label: "已有分镜图" };
  }
  return { ready: false, label: "首尾帧待生成" };
}

export function hasClipVideo(
  clip: TimelineClip,
  selectedStoryboard: Record<string, unknown> | null,
) {
  const frame = matchingStoryboardFrame(clip, selectedStoryboard);
  return Boolean(
    mediaUrl(clip, [...VIDEO_KEYS, "file_url"]) ||
      hasAssetLocator(asRecord(clip.asset_ref)) ||
      (frame && mediaUrl(frame, VIDEO_KEYS)),
  );
}

function hasEnvironmentBinding(
  clip: TimelineClip,
  scene: NormalizedScene | null,
) {
  const sourceRefs = asRecord(clip.source_refs);
  return Boolean(
    numberLike(clip.environment_id) ||
      numberLike(clip.scene_environment_id) ||
      numberLike(sourceRefs?.environment_id) ||
      numberLike(sourceRefs?.scene_environment_id) ||
      scene?.environment_id,
  );
}

function hasVirtualIpBinding(clip: TimelineClip) {
  const keys = [
    "virtual_ip_id",
    "virtual_ip_ids",
    "character_virtual_ip_id",
    "character_virtual_ip_ids",
    "character_ids",
  ];
  const sourceRefs = asRecord(clip.source_refs);
  const source = asRecord(clip.source);
  return (
    hasAnyValue(clip, keys) ||
    hasAnyValue(sourceRefs, keys) ||
    hasAnyValue(source, keys)
  );
}

function matchingStoryboardFrame(
  clip: TimelineClip,
  selectedStoryboard: Record<string, unknown> | null,
) {
  const clipIds = new Set(
    [
      getString(clip.clip_id),
      getString(clip.id),
      getString(asRecord(clip.source)?.storyboard_frame_id),
      getString(asRecord(clip.source_refs)?.storyboard_frame_id),
    ].filter(Boolean),
  );
  return (
    storyboardFrames(selectedStoryboard).find((frame) =>
      [
        getString(frame.timeline_clip_id),
        getString(frame.frame_id),
        getString(frame.id),
      ]
        .filter(Boolean)
        .some((value) => clipIds.has(value)),
    ) ?? null
  );
}

function contextStatusLabel(
  environmentReady: boolean,
  virtualIpReady: boolean,
) {
  if (environmentReady && virtualIpReady) return "环境/IP 已绑定";
  if (environmentReady) return "环境已绑定 · IP 待绑定";
  if (virtualIpReady) return "环境待绑定 · IP 已绑定";
  return "环境/IP 待绑定";
}

function hasAnyValue(record: Record<string, unknown> | null, keys: string[]) {
  if (!record) return false;
  return keys.some((key) => {
    const value = record[key];
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === "number") return Number.isFinite(value);
    if (typeof value === "string") return value.trim().length > 0;
    return Boolean(value);
  });
}

function hasAssetLocator(record: Record<string, unknown> | null) {
  if (!record) return false;
  return Boolean(
    getString(record.file_url) ||
      getString(record.url) ||
      getString(record.image_url) ||
      getString(record.video_url) ||
      getString(record.file_path) ||
      getString(record.object_key) ||
      numberLike(record.media_asset_id) ||
      numberLike(record.asset_id),
  );
}

function numberLike(value: unknown) {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}
