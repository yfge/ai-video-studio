import type { ProductionCanvasResolvedContext } from "@/utils/api/types";
import {
  emptyProductionCanvasContext,
  productionCanvasContextDraftFromResolved,
  productionCanvasRequestContext,
} from "./productionCanvasContext";
import {
  mergeProductionCanvasResolvedContext,
  productionCanvasResolvedContextFromOutputs,
} from "./productionCanvasContextMerge";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import {
  canSeedProductionCanvasScopedContext,
  isScopedProductionCanvasMediaNode,
  scopedProductionCanvasContextOutputKeys,
} from "./productionCanvasScopedContext";
import { taskOutputNumber } from "./productionCanvasSkillNodes";
import { productionCanvasReferenceArtifactMatchesContext } from "./productionCanvasReferenceArtifacts";
import { missingProductionCanvasRequiredInputs } from "./productionCanvasRequiredInputs";
export type ProductionCanvasSharedContext = {
  virtual_ip_id?: number;
  environment_id?: number;
  story_id?: number;
  episode_id?: number;
  script_id?: number;
  timeline_id?: number;
  timeline_version?: number;
  clip_id?: string;
  task_id?: number;
  reference_artifacts?: string[];
};
const referenceArtifactPrefixes = ["virtual_ip_image:", "environment_images:"];
function outputNumber(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  return typeof value === "number" && Number.isFinite(value)
    ? value
    : undefined;
}
function outputString(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  return typeof value === "string" && value.trim() ? value : undefined;
}
function completedReferenceArtifact(node: ProductionCanvasNode) {
  if (node.kind === "note" || node.outputs?.task_status !== "completed") {
    return undefined;
  }
  const value = node.outputs?.result_file_path;
  return typeof value === "string" &&
    referenceArtifactPrefixes.some((prefix) => value.startsWith(prefix))
    ? value
    : undefined;
}
export function collectProductionCanvasContext(nodes: ProductionCanvasNode[]) {
  let draft = { ...emptyProductionCanvasContext };
  const referenceArtifacts: string[] = [];
  for (const node of nodes) {
    const outputs = node.outputs;
    const nodeContext = productionCanvasResolvedContextFromOutputs(outputs);
    if (node.kind !== "note" && !isScopedProductionCanvasMediaNode(node)) {
      draft = mergeProductionCanvasResolvedContext(draft, nodeContext);
    }
    const artifact = completedReferenceArtifact(node);
    if (artifact && !referenceArtifacts.includes(artifact)) {
      referenceArtifacts.push(artifact);
    }
  }
  const context = Object.fromEntries(
    Object.entries(productionCanvasRequestContext(draft)).filter(
      ([, value]) => value !== undefined,
    ),
  ) as ProductionCanvasSharedContext;
  const matchingArtifacts = referenceArtifacts.filter((artifact) =>
    productionCanvasReferenceArtifactMatchesContext(
      artifact,
      context.virtual_ip_id,
      context.environment_id,
    ),
  );
  if (matchingArtifacts.length) {
    context.reference_artifacts = matchingArtifacts;
  }
  return context;
}
function contextOutputs(
  context: ProductionCanvasSharedContext,
): Record<string, unknown> {
  return {
    ...(context.virtual_ip_id
      ? { virtual_ip_ids: [context.virtual_ip_id] }
      : {}),
    ...(context.environment_id
      ? { environment_ids: [context.environment_id] }
      : {}),
    ...(context.story_id ? { story_id: context.story_id } : {}),
    ...(context.episode_id ? { episode_id: context.episode_id } : {}),
    ...(context.script_id ? { script_id: context.script_id } : {}),
    ...(context.timeline_id ? { timeline_id: context.timeline_id } : {}),
    ...(context.timeline_version
      ? { timeline_version: context.timeline_version }
      : {}),
    ...(context.clip_id ? { clip_id: context.clip_id } : {}),
    ...(context.task_id ? { task_id: context.task_id } : {}),
    ...(context.reference_artifacts
      ? { reference_artifacts: context.reference_artifacts }
      : {}),
  };
}
function withResolvedContext(
  context: ProductionCanvasSharedContext,
  resolved?: ProductionCanvasResolvedContext | null,
): ProductionCanvasSharedContext {
  if (!resolved) return context;
  const draft = mergeProductionCanvasResolvedContext(
    productionCanvasContextDraftFromResolved(context),
    resolved,
  );
  return Object.fromEntries(
    Object.entries({
      ...productionCanvasRequestContext(draft),
      reference_artifacts: context.reference_artifacts,
    }).filter(([, value]) => value !== null && value !== undefined),
  ) as ProductionCanvasSharedContext;
}
const sharedContextOutputKeys = [
  "virtual_ip_ids",
  "virtual_ip_id",
  "environment_ids",
  "environment_id",
  "story_id",
  "episode_id",
  "script_id",
  "timeline_id",
  "timeline_version",
  "clip_id",
  "placed_timeline_clip_id",
  "selected_output_clip_id",
  "task_id",
] as const;

export function applyProductionCanvasContext(
  nodes: ProductionCanvasNode[],
  resolved?: ProductionCanvasResolvedContext | null,
) {
  const context = withResolvedContext(
    collectProductionCanvasContext(nodes),
    resolved,
  );
  const sharedOutputs = contextOutputs(context);
  return nodes.map((node) => {
    if (!node.skill && !outputString(node.outputs, "source_node_id"))
      return node;
    const scopedMediaNode = isScopedProductionCanvasMediaNode(node);
    const canSeedScopedContext =
      scopedMediaNode &&
      canSeedProductionCanvasScopedContext(node, sharedOutputs);
    const outputs: Record<string, unknown> = { ...node.outputs };
    for (const key of sharedContextOutputKeys) {
      if (
        !(key in sharedOutputs) &&
        (!scopedMediaNode || !scopedProductionCanvasContextOutputKeys.has(key))
      )
        delete outputs[key];
    }
    Object.assign(outputs, sharedOutputs);
    if (scopedMediaNode) {
      for (const key of scopedProductionCanvasContextOutputKeys) {
        if (key === "reference_artifacts") {
          if (outputNumber(node.outputs, "dispatched_task_id")) {
            if (node.outputs && key in node.outputs)
              outputs[key] = node.outputs[key];
          } else if (!sharedOutputs.reference_artifacts) {
            delete outputs[key];
          }
        } else if (node.outputs && key in node.outputs) {
          outputs[key] = node.outputs[key];
        } else if (
          !canSeedScopedContext ||
          key === "task_id" ||
          key === "task_ids"
        ) {
          delete outputs[key];
        }
      }
      const ownClipId =
        outputString(node.outputs, "placed_timeline_clip_id") ||
        outputString(node.outputs, "selected_output_clip_id") ||
        outputString(node.outputs, "clip_id");
      if (ownClipId) outputs.clip_id = ownClipId;
    }
    const ownTaskId =
      node.kind === "note" || outputNumber(node.outputs, "dispatched_task_id")
        ? taskOutputNumber(node.outputs)
        : undefined;
    if (ownTaskId) outputs.task_id = ownTaskId;
    if (!sharedOutputs.reference_artifacts && !scopedMediaNode) {
      delete outputs.reference_artifacts;
    }
    const rawRequiredInputs = outputs.required_inputs;
    const hadRequiredInputs = Array.isArray(rawRequiredInputs);
    const requiredInputs = missingProductionCanvasRequiredInputs(
      rawRequiredInputs,
      outputs,
    );
    if (requiredInputs.length) {
      return {
        ...node,
        outputs: { ...outputs, required_inputs: requiredInputs },
      };
    }
    const readyOutputs = { ...outputs };
    delete readyOutputs.required_inputs;
    return {
      ...node,
      status:
        node.status === "blocked" && hadRequiredInputs ? "ready" : node.status,
      outputs: readyOutputs,
    };
  });
}
