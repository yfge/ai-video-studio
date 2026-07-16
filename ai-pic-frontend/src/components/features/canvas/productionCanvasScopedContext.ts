import type { ProductionCanvasNode } from "./productionCanvasModel";
import { productionCanvasResolvedContextFromOutputs } from "./productionCanvasContextMerge";

function outputString(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  return typeof value === "string" && value.trim() ? value : undefined;
}

export function isScopedProductionCanvasMediaNode(node: ProductionCanvasNode) {
  const skill = node.skill || outputString(node.outputs, "skill");
  const clipStoryboardVideo =
    skill === "video.candidates" &&
    (outputString(node.outputs, "reference_mode") === "clip_storyboard_sheet" ||
      node.outputs?.use_clip_storyboard === true ||
      outputString(node.outputs, "placement_mode") === "explicit_node");
  return (
    ((skill === "image.candidates" || skill === "video.candidates") &&
      ["frame_indexes", "queued_frame_indexes"].some((key) =>
        Array.isArray(node.outputs?.[key]),
      )) ||
    ((skill === "storyboard.candidates" || clipStoryboardVideo) &&
      Boolean(outputString(node.outputs, "clip_id")))
  );
}

export const scopedProductionCanvasContextOutputKeys = new Set([
  "virtual_ip_id",
  "virtual_ip_ids",
  "environment_id",
  "environment_ids",
  "story_id",
  "episode_id",
  "script_id",
  "script_ids",
  "timeline_id",
  "timeline_ids",
  "timeline_version",
  "timeline_versions",
  "clip_id",
  "placed_timeline_clip_id",
  "selected_output_clip_id",
  "task_id",
  "task_ids",
  "reference_artifacts",
]);

const scopedAnchorKeys = [
  "timeline_id",
  "script_id",
  "episode_id",
  "story_id",
  "virtual_ip_id",
] as const;

export function canSeedProductionCanvasScopedContext(
  node: ProductionCanvasNode,
  sharedOutputs: Record<string, unknown>,
) {
  const own = productionCanvasResolvedContextFromOutputs(node.outputs);
  const shared = productionCanvasResolvedContextFromOutputs(sharedOutputs);
  const anchor = scopedAnchorKeys.find((key) => own[key] !== undefined);
  return !anchor || own[anchor] === shared[anchor];
}

export function productionCanvasSharedContextForNode<T>(
  node: ProductionCanvasNode,
  context: T,
) {
  const skill = node.skill || outputString(node.outputs, "skill");
  return node.kind === "note" ||
    skill === "image.candidates" ||
    skill === "storyboard.candidates" ||
    skill === "video.candidates"
    ? undefined
    : context;
}
