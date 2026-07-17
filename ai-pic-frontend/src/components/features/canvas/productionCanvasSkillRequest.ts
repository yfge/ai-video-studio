import type {
  ProductionCanvasProductionContext,
  ProductionCanvasSkillExecuteRequest,
} from "@/utils/api/types";
import {
  emptyProductionCanvasContext,
  productionCanvasRequestContext,
  type ProductionCanvasContextDraft,
} from "./productionCanvasContext";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import {
  firstOutputNumber,
  outputBoolean,
  outputNumber,
  outputNumberArray,
  outputString,
  outputStringArray,
  taskOutputNumber,
} from "./productionCanvasSkillNodes";
import { isScopedProductionCanvasMediaNode } from "./productionCanvasScopedContext";
import { productionCanvasReferenceArtifactMatchesContext } from "./productionCanvasReferenceArtifacts";

export function productionCanvasSkillExecuteRequest({
  context,
  currentRunId,
  executionScope,
  fallbackPrompt,
  node,
  prompt,
  targetRunId,
}: {
  context: ProductionCanvasContextDraft;
  currentRunId?: string | null;
  executionScope: "node" | "downstream";
  fallbackPrompt?: string;
  node: ProductionCanvasNode;
  prompt: string;
  targetRunId?: string | null;
}): ProductionCanvasSkillExecuteRequest {
  const requestContext = productionCanvasRequestContext(
    fallbackPrompt ? emptyProductionCanvasContext : context,
  );
  const nodeContextFallback = Boolean(fallbackPrompt);
  const scopedMediaNode = isScopedProductionCanvasMediaNode(node);
  const nodeNumber = (key: string) =>
    nodeContextFallback || scopedMediaNode
      ? outputNumber(node.outputs, key)
      : undefined;
  const nodeString = (key: string) =>
    nodeContextFallback || scopedMediaNode
      ? outputString(node.outputs, key)
      : undefined;
  const nodeVirtualIpId =
    nodeNumber("virtual_ip_id") ||
    (nodeContextFallback || scopedMediaNode
      ? firstOutputNumber(node.outputs, "virtual_ip_ids")
      : undefined);
  const nodeEnvironmentId =
    nodeNumber("environment_id") ||
    (nodeContextFallback || scopedMediaNode
      ? firstOutputNumber(node.outputs, "environment_ids")
      : undefined);
  const virtualIpId = scopedMediaNode
    ? nodeVirtualIpId
    : requestContext.virtual_ip_id || nodeVirtualIpId;
  const environmentId = scopedMediaNode
    ? nodeEnvironmentId
    : requestContext.environment_id || nodeEnvironmentId;
  const referenceArtifacts = outputStringArray(
    node.outputs,
    "reference_artifacts",
  )?.filter((value) =>
    productionCanvasReferenceArtifactMatchesContext(
      value,
      virtualIpId,
      environmentId,
    ),
  );
  const planningMode = outputString(node.outputs, "planning_mode");
  const productionContext =
    node.outputs?.production_context &&
    typeof node.outputs.production_context === "object"
      ? (node.outputs.production_context as ProductionCanvasProductionContext)
      : undefined;
  return {
    prompt:
      fallbackPrompt ||
      prompt.trim() ||
      outputString(node.outputs, "prompt") ||
      node.title,
    skill: node.skill || "",
    planning_mode: planningMode === "single_video" ? "single_video" : undefined,
    node_id: node.id,
    execution_scope: executionScope,
    run_id:
      (targetRunId || "").trim() || (currentRunId || "").trim() || undefined,
    reference_artifacts: referenceArtifacts,
    frame_indexes:
      outputNumberArray(node.outputs, "frame_indexes") ||
      outputNumberArray(node.outputs, "queued_frame_indexes"),
    model: outputString(node.outputs, "model"),
    aspect_ratio: outputString(node.outputs, "aspect_ratio"),
    require_reference_images: outputBoolean(
      node.outputs,
      "require_reference_images",
    ),
    duration: outputNumber(node.outputs, "duration"),
    fps: outputNumber(node.outputs, "fps"),
    resolution: outputString(node.outputs, "resolution"),
    ratio: outputString(node.outputs, "ratio"),
    camera_fixed: outputBoolean(node.outputs, "camera_fixed"),
    production_context: productionContext,
    virtual_ip_id: virtualIpId,
    environment_id: environmentId,
    story_id: scopedMediaNode
      ? nodeNumber("story_id")
      : requestContext.story_id || nodeNumber("story_id"),
    episode_id: scopedMediaNode
      ? nodeNumber("episode_id")
      : requestContext.episode_id || nodeNumber("episode_id"),
    script_id: scopedMediaNode
      ? nodeNumber("script_id")
      : requestContext.script_id || nodeNumber("script_id"),
    timeline_id: scopedMediaNode
      ? nodeNumber("timeline_id")
      : requestContext.timeline_id || nodeNumber("timeline_id"),
    timeline_version:
      (scopedMediaNode ? nodeNumber("timeline_version") : undefined) ||
      (!scopedMediaNode
        ? requestContext.timeline_version || nodeNumber("timeline_version")
        : undefined),
    clip_id:
      (scopedMediaNode ? nodeString("clip_id") : undefined) ||
      (!scopedMediaNode
        ? requestContext.clip_id || nodeString("clip_id")
        : undefined),
    task_id: scopedMediaNode
      ? taskOutputNumber(node.outputs)
      : requestContext.task_id ||
        (nodeContextFallback ? taskOutputNumber(node.outputs) : undefined),
  };
}
