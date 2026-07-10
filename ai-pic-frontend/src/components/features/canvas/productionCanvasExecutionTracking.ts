import type { Task } from "@/utils/api/types";
import type { ProductionCanvasNode } from "./productionCanvasModel";

export type TrackedProductionCanvasExecution = {
  skillNode: ProductionCanvasNode;
  taskNode: ProductionCanvasNode;
};

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
): ProductionCanvasNode[] {
  const status = canvasStatusFromTask(task.status);
  const outputs = taskOutputs(task);
  const detail = taskDetail(task);
  return [
    {
      ...execution.skillNode,
      status,
      detail,
      outputs: { ...execution.skillNode.outputs, ...outputs },
    },
    {
      ...execution.taskNode,
      title: task.title || execution.taskNode.title,
      status,
      detail,
      outputs: { ...execution.taskNode.outputs, ...outputs },
    },
  ];
}

export function productionCanvasExecutionFailure(
  execution: TrackedProductionCanvasExecution,
  taskId: number,
  error: string | null,
): ProductionCanvasNode[] {
  const message = error || "未知错误";
  const outputs = {
    task_id: taskId,
    task_status: "failed",
    task_error_message: message,
  };
  return [
    {
      ...execution.skillNode,
      status: "blocked",
      detail: `任务 #${taskId} 失败；错误：${message}`,
      outputs: { ...execution.skillNode.outputs, ...outputs },
    },
    {
      ...execution.taskNode,
      status: "blocked",
      detail: `任务 #${taskId} 失败；错误：${message}`,
      outputs: { ...execution.taskNode.outputs, ...outputs },
    },
  ];
}

function terminalTaskEvidence(node: ProductionCanvasNode) {
  const taskId = node.outputs?.task_id;
  const taskStatus = node.outputs?.task_status;
  if (
    node.kind !== "note" ||
    typeof taskId !== "number" ||
    !["completed", "failed", "cancelled"].includes(String(taskStatus))
  ) {
    return null;
  }
  const explicitSourceId = node.outputs?.source_node_id;
  const suffix = `-task-${taskId}`;
  const sourceNodeId =
    typeof explicitSourceId === "string" && explicitSourceId
      ? explicitSourceId
      : node.id.endsWith(suffix)
      ? node.id.slice(0, -suffix.length)
      : "";
  return sourceNodeId ? { node, sourceNodeId, taskId, taskStatus } : null;
}

export function reconcileProductionCanvasExecutionTasks(
  nodes: ProductionCanvasNode[],
) {
  const evidenceByExecution = new Map<
    string,
    NonNullable<ReturnType<typeof terminalTaskEvidence>>
  >();
  for (const node of nodes) {
    const evidence = terminalTaskEvidence(node);
    if (evidence) {
      evidenceByExecution.set(
        `${evidence.sourceNodeId}:${evidence.taskId}`,
        evidence,
      );
    }
  }
  return nodes.map((node) => {
    const dispatchedTaskId = node.outputs?.dispatched_task_id;
    const evidence = evidenceByExecution.get(`${node.id}:${dispatchedTaskId}`);
    if (!evidence) {
      return node;
    }
    return {
      ...node,
      status:
        evidence.taskStatus === "completed"
          ? ("review" as const)
          : ("blocked" as const),
      detail: evidence.node.detail || node.detail,
      outputs: { ...node.outputs, ...evidence.node.outputs },
    };
  });
}
