import type { ProductionCanvasNode } from "./productionCanvasModel";

export const COLLAPSED_TASK_LIMIT = 4;
export const EXPANDED_TASK_LIMIT = 20;
export type TaskSummaryFilter = "all" | "running" | "completed" | "failed";

const taskStatusLabels: Record<string, string> = {
  blocked: "异常",
  cancelled: "已取消",
  completed: "已完成",
  failed: "失败",
  pending: "等待中",
  processing: "生成中",
  ready: "可复用",
  review: "待选择",
  running: "生成中",
};

export function taskStatus(node: ProductionCanvasNode) {
  const value = node.outputs?.task_status;
  return typeof value === "string" ? value : node.status;
}

export function taskStatusLabel(node: ProductionCanvasNode) {
  const status = taskStatus(node);
  return taskStatusLabels[status] || status;
}

export function taskTitle(node: ProductionCanvasNode) {
  const value = node.outputs?.task_title;
  return typeof value === "string" && value.trim() ? value : node.title;
}

export function taskExtra(node: ProductionCanvasNode) {
  const error = node.outputs?.task_error_message;
  if (typeof error === "string" && error.trim()) {
    return { label: `错误：${error}`, tone: "red" };
  }
  const progress = node.outputs?.task_progress_detail;
  if (typeof progress === "string" && progress.trim()) {
    return { label: `进度：${progress}`, tone: "gray" };
  }
  return null;
}

export function taskAction(node: ProductionCanvasNode, taskId: number) {
  const label = node.actionLabel || "打开";
  return {
    ariaLabel: node.actionLabel ? `${label} ${taskId}` : `打开任务 ${taskId}`,
    label,
  };
}
