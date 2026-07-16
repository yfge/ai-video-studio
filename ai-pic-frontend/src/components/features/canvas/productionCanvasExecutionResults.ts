import type {
  ProductionCanvasNodeExecutionResponse,
  ProductionCanvasResolvedContext,
  ProductionCanvasSkillExecuteResponse,
} from "@/utils/api/types";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import {
  productionCanvasContextOutputPatch,
  productionCanvasResolvedContextFromOutputs,
} from "./productionCanvasContextMerge";
import {
  productionCanvasSkillResultToNode,
  productionCanvasSkillResultToTaskNode,
} from "./productionCanvasSkillNodes";

export type ProductionCanvasExecutionPublication = {
  resolvedContext: ProductionCanvasResolvedContext;
  sourceNode: ProductionCanvasNode;
  resultNodes: ProductionCanvasNode[];
};

const contextKeys = [
  "virtual_ip_id",
  "environment_id",
  "story_id",
  "episode_id",
  "script_id",
  "timeline_id",
  "timeline_version",
  "clip_id",
  "task_id",
] as const;

function executionOutputs(
  execution: ProductionCanvasNodeExecutionResponse,
  sourceNode: ProductionCanvasNode,
) {
  const incoming = {
    ...execution.skill_result.outputs,
    ...(execution.task_id ? { task_id: execution.task_id } : {}),
    ...(execution.resolved_context_revision
      ? { resolved_context_revision: execution.resolved_context_revision }
      : {}),
  };
  if (!execution.resolved_context) return incoming;
  const resolvedPatch = productionCanvasContextOutputPatch(
    sourceNode.outputs,
    execution.resolved_context,
  );
  const resolvedOutputs = { ...sourceNode.outputs, ...resolvedPatch };
  const resultPatch = productionCanvasContextOutputPatch(
    resolvedOutputs,
    productionCanvasResolvedContextFromOutputs(incoming),
  );
  return { ...incoming, ...resolvedPatch, ...resultPatch };
}

function finalExecutionContext(
  execution: ProductionCanvasNodeExecutionResponse,
  outputs: Record<string, unknown>,
) {
  const context = productionCanvasResolvedContextFromOutputs(outputs);
  if (
    !execution.resolved_context ||
    !contextKeys.every((key) => key in execution.resolved_context!)
  ) {
    return context;
  }
  return Object.fromEntries(
    contextKeys.map((key) => [key, context[key] ?? null]),
  ) as ProductionCanvasResolvedContext;
}

export function productionCanvasExecutionPublications(
  response: ProductionCanvasSkillExecuteResponse,
  requestedNode: ProductionCanvasNode,
  nodes: ProductionCanvasNode[],
): ProductionCanvasExecutionPublication[] {
  const executions: ProductionCanvasNodeExecutionResponse[] = response
    .executions?.length
    ? response.executions
    : [response];
  return executions.map((execution) => {
    const sourceNode =
      execution.node_id === requestedNode.id
        ? requestedNode
        : nodes.find((node) => node.id === execution.node_id) || requestedNode;
    const outputs = executionOutputs(execution, sourceNode);
    const skillResult = { ...execution.skill_result, outputs };
    const skillNode = {
      ...productionCanvasSkillResultToNode(sourceNode, skillResult),
      executionInputFingerprint:
        execution.input_fingerprint || sourceNode.executionInputFingerprint,
    };
    const taskNode = productionCanvasSkillResultToTaskNode(
      sourceNode,
      skillResult,
      execution,
    );
    return {
      resolvedContext: finalExecutionContext(execution, outputs),
      sourceNode,
      resultNodes: taskNode ? [skillNode, taskNode] : [skillNode],
    };
  });
}
