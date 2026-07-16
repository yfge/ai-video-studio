import type { ProductionCanvasResolvedContext, Task } from "@/utils/api/types";
import { productionCanvasContextOutputPatch } from "./productionCanvasContextMerge";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import {
  productionCanvasTaskStatusLabel,
  taskOutputNumber,
} from "./productionCanvasSkillNodes";
import { isScopedProductionCanvasMediaNode } from "./productionCanvasScopedContext";

const scopedContextKeys = [
  "virtual_ip_id",
  "virtual_ip_ids",
  "environment_id",
  "environment_ids",
  "story_id",
  "episode_id",
  "script_id",
  "timeline_id",
  "timeline_version",
  "clip_id",
  "placed_timeline_clip_id",
  "selected_output_clip_id",
] as const;

function canvasStatusFromTask(
  status: Task["status"],
): ProductionCanvasNode["status"] {
  if (status === "failed" || status === "cancelled") return "blocked";
  if (status === "completed") return "review";
  return "running";
}

function taskDetail(task: Task) {
  const parts = [
    `任务 #${task.id} 当前状态 ${productionCanvasTaskStatusLabel(task.status)}`,
  ];
  if (task.progress_detail) parts.push(`进度：${task.progress_detail}`);
  if (task.error_message) parts.push(`错误：${task.error_message}`);
  return parts.join("；");
}

export function productionCanvasTaskNodePatch(
  node: ProductionCanvasNode,
  task: Task,
  context: ProductionCanvasResolvedContext,
): Partial<ProductionCanvasNode> {
  const contextOutputs = productionCanvasContextOutputPatch(node.outputs, {
    ...context,
    task_id: task.id,
  });
  if (isScopedProductionCanvasMediaNode(node)) {
    for (const key of scopedContextKeys) {
      if (node.outputs && key in node.outputs)
        contextOutputs[key] = node.outputs[key];
    }
  }
  return {
    title: node.kind === "note" ? task.title : node.title,
    status: canvasStatusFromTask(task.status),
    detail: taskDetail(task),
    outputs: {
      ...contextOutputs,
      task_id: task.id,
      task_status: task.status,
      task_title: task.title,
      task_type: task.task_type,
      task_prompt: task.prompt,
      task_description: task.description,
      task_progress_detail: task.progress_detail,
      task_error_message: task.error_message,
      task_updated_at: task.updated_at,
      ...(task.result_file_path
        ? { result_file_path: task.result_file_path }
        : {}),
    },
    actionHref: `/tasks?task_id=${task.id}`,
    actionLabel: "查看任务",
  };
}

export function productionCanvasTaskRefreshErrorPatch(
  taskId: number,
  message: string,
): Partial<ProductionCanvasNode> {
  return {
    status: "blocked",
    detail: `任务 #${taskId} 刷新失败：${message}`,
    outputs: { task_status: "blocked", task_error_message: message },
  };
}

export function productionCanvasCurrentTaskSource(
  node: ProductionCanvasNode,
  nodes: ProductionCanvasNode[],
  taskId: number,
) {
  if (node.kind !== "note") {
    return taskOutputNumber(node.outputs) === taskId ? node : undefined;
  }
  const sourceId = node.outputs?.source_node_id;
  if (typeof sourceId !== "string") return undefined;
  const source = nodes.find((candidate) => candidate.id === sourceId);
  return source && taskOutputNumber(source.outputs) === taskId
    ? source
    : undefined;
}
