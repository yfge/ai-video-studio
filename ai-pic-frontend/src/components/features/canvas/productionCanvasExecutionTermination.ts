import { outputNumber, taskOutputNumber } from "./productionCanvasSkillNodes";
import type { TrackedProductionCanvasExecution } from "./productionCanvasExecutionTracking";

function updateExecution(
  execution: TrackedProductionCanvasExecution,
  status: "blocked" | "stale",
  detail: string,
  outputs: Record<string, unknown>,
) {
  return [execution.skillNode, execution.taskNode].map((node) => ({
    ...node,
    status,
    detail,
    outputs: { ...node.outputs, ...outputs },
  }));
}

export function productionCanvasExecutionFailure(
  execution: TrackedProductionCanvasExecution,
  taskId: number,
  error: string | null,
  taskStatus: "failed" | "cancelled" | "timeout" = "failed",
) {
  const message =
    error || (taskStatus === "cancelled" ? "任务已取消" : "未知错误");
  const statusLabel =
    taskStatus === "cancelled"
      ? "已取消"
      : taskStatus === "timeout"
      ? "等待超时"
      : "失败";
  return updateExecution(
    execution,
    "blocked",
    `任务 #${taskId} ${statusLabel}；${message}`,
    {
      task_id: taskId,
      task_status: taskStatus,
      task_error_message: message,
    },
  );
}

export function productionCanvasExecutionStale(
  execution: TrackedProductionCanvasExecution,
) {
  const taskId = taskOutputNumber(execution.taskNode.outputs);
  const renderJobId = outputNumber(execution.taskNode.outputs, "render_job_id");
  return updateExecution(
    execution,
    "stale",
    "当前主链上下文已切换，旧执行结果未写入当前分支。",
    {
      ...(taskId ? { task_id: taskId, task_status: "stale" } : {}),
      ...(renderJobId
        ? { render_job_id: renderJobId, render_status: "stale" }
        : {}),
    },
  );
}

export function productionCanvasRenderTimeout(
  execution: TrackedProductionCanvasExecution,
) {
  const renderJobId = outputNumber(execution.taskNode.outputs, "render_job_id");
  return updateExecution(
    execution,
    "blocked",
    `Render #${renderJobId || "?"} 等待超时，请刷新状态后重试。`,
    { render_status: "timeout" },
  );
}
