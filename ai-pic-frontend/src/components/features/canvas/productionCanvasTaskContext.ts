function outputNumber(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  return typeof value === "number" && Number.isFinite(value)
    ? value
    : undefined;
}

export function outputTaskContext(
  outputs: Record<string, unknown> | undefined,
) {
  const canvasTaskId = outputNumber(outputs, "canvas_task_id");
  const dispatchedTaskId = outputNumber(outputs, "dispatched_task_id");
  const taskId = outputNumber(outputs, "task_id");

  if (dispatchedTaskId && dispatchedTaskId !== canvasTaskId) {
    return dispatchedTaskId;
  }
  if (taskId && taskId !== canvasTaskId) return taskId;
  return undefined;
}
