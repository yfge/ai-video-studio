import type { ProductionCanvasNode } from "./productionCanvasModel";
import { outputTaskContext } from "./productionCanvasTaskContext";

type ProductionCanvasSharedContext = {
  virtual_ip_id?: number;
  environment_id?: number;
  episode_id?: number;
  script_id?: number;
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

function firstOutputNumber(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  if (!Array.isArray(value)) return undefined;
  const first = value.find((item) => typeof item === "number");
  return typeof first === "number" ? first : undefined;
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

function collectCanvasContext(nodes: ProductionCanvasNode[]) {
  const context: ProductionCanvasSharedContext = {};
  const referenceArtifacts: string[] = [];
  for (const node of nodes) {
    const outputs = node.outputs;
    const virtualIpId = firstOutputNumber(outputs, "virtual_ip_ids");
    const environmentId = firstOutputNumber(outputs, "environment_ids");
    const episodeId = outputNumber(outputs, "episode_id");
    const scriptId = outputNumber(outputs, "script_id");
    const taskContextId = outputTaskContext(outputs);

    if (virtualIpId) context.virtual_ip_id = virtualIpId;
    if (environmentId) context.environment_id = environmentId;
    if (episodeId) context.episode_id = episodeId;
    if (scriptId) context.script_id = scriptId;
    if (taskContextId) context.task_id = taskContextId;
    const artifact = completedReferenceArtifact(node);
    if (artifact && !referenceArtifacts.includes(artifact)) {
      referenceArtifacts.push(artifact);
    }
  }
  if (referenceArtifacts.length) {
    context.reference_artifacts = referenceArtifacts;
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
    ...(context.episode_id ? { episode_id: context.episode_id } : {}),
    ...(context.script_id ? { script_id: context.script_id } : {}),
    ...(context.task_id ? { task_id: context.task_id } : {}),
    ...(context.reference_artifacts
      ? { reference_artifacts: context.reference_artifacts }
      : {}),
  };
}

function requiredInputSatisfied(
  input: unknown,
  outputs: Record<string, unknown>,
) {
  if (input === "virtual_ip_id") {
    return firstOutputNumber(outputs, "virtual_ip_ids");
  }
  if (input === "environment_id") {
    return firstOutputNumber(outputs, "environment_ids");
  }
  if (input === "reference_artifacts") {
    return (
      Array.isArray(outputs.reference_artifacts) &&
      outputs.reference_artifacts.length > 0
    );
  }
  if (typeof input === "string") return outputNumber(outputs, input);
  return false;
}

export function applyProductionCanvasContext(nodes: ProductionCanvasNode[]) {
  const sharedOutputs = contextOutputs(collectCanvasContext(nodes));
  return nodes.map((node) => {
    if (!node.skill) return node;
    const outputs: Record<string, unknown> = {
      ...node.outputs,
      ...sharedOutputs,
    };
    if (
      (node.skill === "image.candidates" ||
        node.skill === "video.candidates") &&
      Array.isArray(node.outputs?.frame_indexes) &&
      outputNumber(node.outputs, "script_id")
    ) {
      outputs.script_id = node.outputs?.script_id;
    }
    if (!sharedOutputs.reference_artifacts) {
      delete outputs.reference_artifacts;
    }
    const rawRequiredInputs = outputs.required_inputs;
    const hadRequiredInputs = Array.isArray(rawRequiredInputs);
    const requiredInputs = hadRequiredInputs
      ? rawRequiredInputs.filter(
          (input) => !requiredInputSatisfied(input, outputs),
        )
      : [];
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
