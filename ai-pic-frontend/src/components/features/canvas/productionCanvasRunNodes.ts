import type {
  ProductionCanvasPlanNode,
  ProductionCanvasRunResponse,
  ProductionCanvasSavedNode,
} from "@/utils/api/types";
import { finiteCanvasNumber } from "./productionCanvasGeometry";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { withProductionCanvasPortContract } from "./productionCanvasPorts";

function runOutputs(run: ProductionCanvasRunResponse) {
  return {
    ...(run.run_id ? { canvas_run_id: run.run_id } : {}),
    ...(run.task_id ? { canvas_task_id: run.task_id } : {}),
  };
}

export function planNodeToCanvasNode(
  node: ProductionCanvasPlanNode,
  run: ProductionCanvasRunResponse,
): ProductionCanvasNode {
  return withProductionCanvasPortContract({
    id: node.id,
    label: node.label,
    title: node.title,
    status: node.status,
    x: finiteCanvasNumber(node.x, 0),
    y: finiteCanvasNumber(node.y, 0),
    width: finiteCanvasNumber(node.width, 220),
    height:
      node.height === undefined
        ? undefined
        : finiteCanvasNumber(node.height, 118),
    kind: node.kind || "skill_result",
    skill: node.skill,
    detail: node.detail,
    outputs: { ...node.outputs, ...runOutputs(run) },
    reuseTargets: node.reuse_targets,
    actionHref: node.action_href || undefined,
    actionLabel: node.action_label || undefined,
    definitionVersion: node.definition_version,
    inputPorts: node.input_ports?.map((port) => ({
      ...port,
      label: port.id,
    })),
    outputPorts: node.output_ports?.map((port) => ({
      ...port,
      label: port.id,
    })),
  });
}

export function savedNodeToCanvasNode(
  node: ProductionCanvasSavedNode,
  run?: ProductionCanvasRunResponse,
): ProductionCanvasNode {
  return withProductionCanvasPortContract({
    id: node.id,
    label: node.label,
    title: node.title,
    status: node.status,
    x: finiteCanvasNumber(node.x, 0),
    y: finiteCanvasNumber(node.y, 0),
    width: finiteCanvasNumber(node.width, 190),
    height: node.height ? finiteCanvasNumber(node.height, 96) : undefined,
    kind: node.kind || undefined,
    skill: node.skill || undefined,
    detail: node.detail || undefined,
    outputs: normalizeSavedNodeOutputsForRun(node, run),
    reuseTargets: node.reuse_targets,
    actionHref: node.action_href || undefined,
    actionLabel: node.action_label || undefined,
    definitionVersion: node.definition_version,
    inputPorts: node.input_ports?.map((port) => ({
      ...port,
      label: port.id,
    })),
    outputPorts: node.output_ports?.map((port) => ({
      ...port,
      label: port.id,
    })),
  });
}

function savedOutputString(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  return typeof value === "string" && value.trim() ? value.trim() : "";
}

function savedOutputNumber(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  return typeof value === "number" && Number.isFinite(value)
    ? value
    : undefined;
}

function isSavedNodeFromDifferentRun(
  node: ProductionCanvasSavedNode,
  run: ProductionCanvasRunResponse,
) {
  const currentRunId = run.run_id?.trim();
  const nodeRunId = savedOutputString(node.outputs, "canvas_run_id");
  return Boolean(currentRunId && nodeRunId && nodeRunId !== currentRunId);
}

function savedTaskContextId(node: ProductionCanvasSavedNode) {
  return (
    savedOutputNumber(node.outputs, "dispatched_task_id") ??
    savedOutputNumber(node.outputs, "task_id")
  );
}

function isSavedNodeUnscopedToRun(
  node: ProductionCanvasSavedNode,
  run: ProductionCanvasRunResponse,
) {
  const currentRunId = run.run_id?.trim();
  const nodeRunId = savedOutputString(node.outputs, "canvas_run_id");
  return Boolean(currentRunId && !nodeRunId && savedTaskContextId(node));
}

function normalizeSavedNodeOutputsForRun(
  node: ProductionCanvasSavedNode,
  run?: ProductionCanvasRunResponse,
) {
  const outputs: Record<string, unknown> = { ...(node.outputs || {}) };
  if (!run || (node.kind !== "skill_result" && !node.skill)) return outputs;

  const previousCanvasTaskId = savedOutputNumber(outputs, "canvas_task_id");
  const taskId = savedOutputNumber(outputs, "task_id");
  const dispatchedTaskId = savedOutputNumber(outputs, "dispatched_task_id");
  const scopedOutputs = runOutputs(run);

  if (
    previousCanvasTaskId &&
    previousCanvasTaskId !== run.task_id &&
    taskId === previousCanvasTaskId
  ) {
    delete outputs.task_id;
  }
  if (
    previousCanvasTaskId &&
    previousCanvasTaskId !== run.task_id &&
    dispatchedTaskId === previousCanvasTaskId
  ) {
    delete outputs.dispatched_task_id;
  }

  return { ...outputs, ...scopedOutputs };
}

function planNodeWithSavedLayout(
  node: ProductionCanvasPlanNode,
  savedNode: ProductionCanvasSavedNode,
): ProductionCanvasPlanNode {
  return {
    ...node,
    x: finiteCanvasNumber(savedNode.x, node.x),
    y: finiteCanvasNumber(savedNode.y, node.y),
    width: finiteCanvasNumber(savedNode.width, node.width),
    height:
      savedNode.height === undefined || savedNode.height === null
        ? node.height
        : finiteCanvasNumber(savedNode.height, node.height || 118),
  };
}

export function restoredSavedNode(
  node: ProductionCanvasSavedNode,
  run: ProductionCanvasRunResponse,
  planNodesById: Map<string, ProductionCanvasPlanNode>,
) {
  if (
    !isSavedNodeFromDifferentRun(node, run) &&
    !isSavedNodeUnscopedToRun(node, run)
  ) {
    return savedNodeToCanvasNode(node, run);
  }

  const planNode = planNodesById.get(node.id);
  if (!planNode) return null;
  return planNodeToCanvasNode(planNodeWithSavedLayout(planNode, node), run);
}
