"use client";

interface StatusLineTask {
  taskId: number;
  phase: string;
  error: string | null;
}

/**
 * Inline progress line for one tracked generation task, shown next to the
 * submit control so operators never have to leave for the task list.
 */
export function GenerationTaskStatusLine({
  label,
  task,
}: {
  label: string;
  task?: StatusLineTask | null;
}) {
  if (!task) return null;
  if (task.phase === "pending" || task.phase === "processing") {
    return (
      <div
        className="mt-2 flex items-center gap-2 rounded-md bg-blue-50 px-2 py-1.5 text-xs text-blue-700"
        role="status"
      >
        <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
        <span>
          {label}生成中（任务 #{task.taskId}），完成后自动刷新…
        </span>
      </div>
    );
  }
  if (task.phase === "completed") {
    return (
      <div className="mt-2 rounded-md bg-green-50 px-2 py-1.5 text-xs text-green-700">
        {label}已生成完成（任务 #{task.taskId}）
      </div>
    );
  }
  if (task.phase === "failed") {
    return (
      <div className="mt-2 rounded-md bg-red-50 px-2 py-1.5 text-xs text-red-700">
        {label}生成失败（任务 #{task.taskId}）：{task.error || "未知错误"}
      </div>
    );
  }
  if (task.phase === "timeout") {
    return (
      <div className="mt-2 rounded-md bg-amber-50 px-2 py-1.5 text-xs text-amber-700">
        {label}任务 #{task.taskId} 等待超时，请稍后在任务列表查看
      </div>
    );
  }
  return null;
}
