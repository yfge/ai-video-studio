import { asRecord, getString } from "@/hooks/useEpisodeDetail";
import type { NormalizedScene } from "@/utils/api/types";

function timelineSceneNumber(meta: Record<string, unknown>) {
  const raw =
    getString(meta.scene_number) ||
    getString(asRecord(meta.source)?.scene_number) ||
    getString(asRecord(meta.source_refs)?.scene_number) ||
    getString(meta.scene);
  if (raw) return raw.replace(/^scene-/i, "");
  const index = Number(meta.scene_index);
  return Number.isFinite(index) ? String(index + 1) : null;
}

function timelineSceneId(meta: Record<string, unknown>) {
  const raw =
    meta.scene_id ??
    asRecord(meta.source)?.scene_id ??
    asRecord(meta.source_refs)?.scene_id;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : null;
}

export function sceneForTimelineMeta(
  scenes: NormalizedScene[],
  meta: Record<string, unknown>,
  overrides: Record<number, number | null> = {},
) {
  const sceneNumber = timelineSceneNumber(meta);
  const sceneId = timelineSceneId(meta);
  const matched =
    (sceneNumber
      ? scenes.find(
          (scene) => String(scene.scene_number) === String(sceneNumber),
        )
      : null) ||
    (sceneId != null ? scenes.find((scene) => scene.id === sceneId) : null) ||
    (sceneId != null
      ? scenes.find((scene) => String(scene.scene_number) === String(sceneId))
      : null);
  if (!matched) return null;
  return {
    ...matched,
    environment_id: Object.prototype.hasOwnProperty.call(overrides, matched.id)
      ? overrides[matched.id]
      : matched.environment_id,
  };
}
