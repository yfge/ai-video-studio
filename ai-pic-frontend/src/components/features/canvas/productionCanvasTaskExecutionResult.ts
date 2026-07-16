import type { ProductionCanvasResolvedContext, Task } from "@/utils/api/types";
import { productionCanvasContextOutputPatch } from "./productionCanvasContextMerge";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { isScopedProductionCanvasMediaNode } from "./productionCanvasScopedContext";
import type { TrackedProductionCanvasExecution } from "./productionCanvasExecutionTracking";

function canvasStatusFromTask(
  status: Task["status"],
): ProductionCanvasNode["status"] {
  if (status === "completed") return "review";
  if (status === "failed" || status === "cancelled") return "blocked";
  return "running";
}

function taskOutputs(task: Task) {
  return {
    task_id: task.id,
    task_status: task.status,
    task_title: task.title,
    task_type: task.task_type,
    task_progress_detail: task.progress_detail,
    task_error_message: task.error_message,
    task_updated_at: task.updated_at,
    ...(task.result_file_path
      ? { result_file_path: task.result_file_path }
      : {}),
  };
}

const scopedContextKeys = [
  "script_id",
  "timeline_id",
  "timeline_version",
  "clip_id",
  "placed_timeline_clip_id",
  "selected_output_clip_id",
] as const;

function taskContextOutputs(
  node: ProductionCanvasNode,
  resolvedContext: ProductionCanvasResolvedContext,
) {
  const outputs: Record<string, unknown> = {
    ...node.outputs,
    ...productionCanvasContextOutputPatch(node.outputs, resolvedContext),
  };
  if (isScopedProductionCanvasMediaNode(node)) {
    for (const key of scopedContextKeys) {
      if (node.outputs && key in node.outputs) outputs[key] = node.outputs[key];
    }
  }
  return outputs;
}

function taskDetail(task: Task) {
  const parts = [
    `任务 #${task.id} ${task.status === "completed" ? "已完成" : "失败"}`,
  ];
  if (task.result_file_path) parts.push(`产物：${task.result_file_path}`);
  if (task.error_message) parts.push(`错误：${task.error_message}`);
  return parts.join("；");
}

export function productionCanvasExecutionFromTask(
  execution: TrackedProductionCanvasExecution,
  task: Task,
  resolvedContext: ProductionCanvasResolvedContext = {},
): ProductionCanvasNode[] {
  const status = canvasStatusFromTask(task.status);
  const detail = taskDetail(task);
  return [execution.skillNode, execution.taskNode].map((node) => {
    const outputs: Record<string, unknown> = {
      ...taskContextOutputs(node, {
        ...resolvedContext,
        task_id: task.id,
      }),
      ...taskOutputs(task),
    };
    Object.keys(outputs).forEach((key) => {
      if (outputs[key] === undefined) delete outputs[key];
    });
    return {
      ...node,
      title: node.kind === "note" ? task.title || node.title : node.title,
      status,
      detail,
      outputs,
    };
  });
}
