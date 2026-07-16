import type {
  ProductionCanvasNodeExecutionResponse,
  ProductionCanvasPlanNode,
  ProductionCanvasPlanResponse,
  ProductionCanvasSkillExecuteResponse,
  ProductionCanvasSkillResult,
} from "@/utils/api/types";
import {
  productionCanvasStatusMeta,
  type ProductionCanvasNode,
} from "./productionCanvasModel";
import { taskStatusLabelForStatus } from "./productionCanvasTaskSummaryModel";
import { withProductionCanvasPortContract } from "./productionCanvasPorts";
import {
  productionCanvasContextOutputPatch,
  productionCanvasResolvedContextFromOutputs,
} from "./productionCanvasContextMerge";

function runOutputs(response: ProductionCanvasPlanResponse) {
  return {
    ...(response.run_id ? { canvas_run_id: response.run_id } : {}),
    ...(response.task_id ? { canvas_task_id: response.task_id } : {}),
  };
}

export function productionCanvasPlanNodeToCanvasNode(
  node: ProductionCanvasPlanNode,
  response: ProductionCanvasPlanResponse,
  contextOutputs: Record<string, unknown> = {},
): ProductionCanvasNode {
  return withProductionCanvasPortContract({
    id: node.id,
    label: node.label,
    title: node.title,
    status: node.status,
    x: node.x,
    y: node.y,
    width: node.width,
    height: node.height,
    kind: node.kind || "skill_result",
    skill: node.skill,
    detail: node.detail,
    outputs: { ...contextOutputs, ...node.outputs, ...runOutputs(response) },
    reuseTargets: node.reuse_targets,
    actionHref: node.action_href || undefined,
    actionLabel: node.action_label || undefined,
  });
}

export function outputString(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  return typeof value === "string" && value.trim() ? value : undefined;
}

export function outputNumber(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  return typeof value === "number" && Number.isFinite(value)
    ? value
    : undefined;
}

export function outputBoolean(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  return typeof value === "boolean" ? value : undefined;
}

export function outputNumberArray(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  if (!Array.isArray(value)) return undefined;
  const numbers = value.filter((item) => typeof item === "number");
  return numbers.length ? numbers : undefined;
}

export function outputStringArray(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  if (!Array.isArray(value)) return undefined;
  const strings = value.filter(
    (item): item is string => typeof item === "string" && Boolean(item.trim()),
  );
  return strings.length ? strings : undefined;
}

export function firstOutputNumber(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  if (!Array.isArray(value)) return undefined;
  const first = value.find((item) => typeof item === "number");
  return typeof first === "number" ? first : undefined;
}

export function taskOutputNumber(outputs: Record<string, unknown> | undefined) {
  return (
    outputNumber(outputs, "dispatched_task_id") ??
    outputNumber(outputs, "task_id") ??
    outputNumber(outputs, "canvas_task_id")
  );
}

export function productionCanvasTaskStatusLabel(status: string) {
  return taskStatusLabelForStatus(status);
}

export function productionCanvasNodeStatusMeta(node: ProductionCanvasNode) {
  const taskStatus =
    node.kind === "note" && taskOutputNumber(node.outputs)
      ? outputString(node.outputs, "task_status")
      : undefined;
  if (!taskStatus) return productionCanvasStatusMeta[node.status];

  const taskStatusTones: Record<
    string,
    "blue" | "green" | "amber" | "red" | "gray"
  > = {
    blocked: "red",
    cancelled: "red",
    completed: "green",
    failed: "red",
    pending: "blue",
    processing: "amber",
    ready: "green",
    review: "blue",
    running: "amber",
  };
  return {
    label: productionCanvasTaskStatusLabel(taskStatus),
    tone: taskStatusTones[taskStatus] || "gray",
  };
}

export function isManualProductionCanvasNote(
  node?: ProductionCanvasNode,
): node is ProductionCanvasNode & { kind: "note" } {
  return Boolean(node?.kind === "note" && !taskOutputNumber(node.outputs));
}

export function productionCanvasSkillResultToNode(
  node: ProductionCanvasNode,
  result: ProductionCanvasSkillResult,
): ProductionCanvasNode {
  const outputUrl = outputString(result.outputs, "output_url");
  const isRenderResult = Boolean(outputNumber(result.outputs, "render_job_id"));
  const previousOutputs = { ...node.outputs };
  if (outputNumber(result.outputs, "dispatched_task_id")) {
    delete previousOutputs.task_error_message;
    delete previousOutputs.task_progress_detail;
    delete previousOutputs.task_updated_at;
    delete previousOutputs.required_inputs;
  }
  const contextPatch = productionCanvasContextOutputPatch(
    previousOutputs,
    productionCanvasResolvedContextFromOutputs(result.outputs),
  );
  return {
    ...node,
    label: result.label,
    title: result.title,
    status: result.status,
    detail: result.detail,
    outputs: { ...previousOutputs, ...contextPatch, ...result.outputs },
    reuseTargets: result.reuse_targets,
    actionHref: outputUrl || (isRenderResult ? undefined : node.actionHref),
    actionLabel: outputUrl
      ? "打开成片"
      : isRenderResult
      ? undefined
      : node.actionLabel,
  };
}

export function productionCanvasSkillResultToTaskNode(
  node: ProductionCanvasNode,
  result: ProductionCanvasSkillResult,
  response:
    | ProductionCanvasSkillExecuteResponse
    | ProductionCanvasNodeExecutionResponse,
): ProductionCanvasNode | null {
  const taskId =
    response.task_id ?? outputNumber(result.outputs, "dispatched_task_id");
  const renderJobId = outputNumber(result.outputs, "render_job_id");
  if (!taskId && !renderJobId) return null;
  const evidenceId = taskId || renderJobId;
  const outputUrl = outputString(result.outputs, "output_url");
  return {
    id: `${node.id}-${taskId ? "task" : "render"}-${evidenceId}`,
    label: taskId ? `Task #${taskId}` : `Render #${renderJobId}`,
    title: result.title,
    status: result.status,
    x: node.x + 36,
    y: node.y + 112,
    width: Math.max(220, node.width),
    kind: "note",
    detail: result.detail,
    outputs: {
      source_node_id: node.id,
      skill: result.skill,
      ...(taskId
        ? { task_id: taskId, task_status: response.task_status }
        : { render_job_id: renderJobId }),
      ...result.outputs,
    },
    reuseTargets: result.reuse_targets,
    actionHref: outputUrl || (taskId ? `/tasks?task_id=${taskId}` : "/stories"),
    actionLabel: outputUrl ? "打开成片" : taskId ? "查看任务" : "查看渲染",
  };
}
