import type { Task, TimelineRenderJobResponse } from "@/utils/api/types";
import type { ProductionCanvasNode } from "./productionCanvasModel";

export type TrackedProductionCanvasExecution = {
  skillNode: ProductionCanvasNode;
  taskNode: ProductionCanvasNode;
};

function renderOutputUrl(job: TimelineRenderJobResponse) {
  return job.output_asset?.file_url || job.output_asset?.file_path || undefined;
}

function renderJobOutputs(job: TimelineRenderJobResponse) {
  return {
    timeline_id: job.timeline_id,
    timeline_version: job.timeline_version,
    render_job_id: job.id,
    render_status: job.status,
    render_progress: job.progress,
    output_asset_id: job.output_asset_id,
    output_url: renderOutputUrl(job),
    render_log: job.log,
    render_updated_at: job.updated_at,
  };
}

export function productionCanvasExecutionFromRenderJob(
  execution: TrackedProductionCanvasExecution,
  job: TimelineRenderJobResponse,
): ProductionCanvasNode[] {
  const outputUrl = renderOutputUrl(job);
  const succeeded = job.status === "succeeded" && Boolean(outputUrl);
  const active = job.status === "queued" || job.status === "running";
  const status = succeeded ? "ready" : active ? "running" : "blocked";
  const title = succeeded
    ? "最终渲染已完成"
    : active
    ? "最终渲染正在执行"
    : job.status === "cancelled"
    ? "最终渲染已取消"
    : "最终渲染失败";
  const detail = succeeded
    ? "成片资产已生成，可直接打开。"
    : active
    ? `后台渲染进度 ${job.progress}%。`
    : "最终渲染未生成可用成片，请重新执行 Render Skill。";
  const outputs = renderJobOutputs(job);
  const action = outputUrl
    ? { actionHref: outputUrl, actionLabel: "打开成片" }
    : {};
  return [execution.skillNode, execution.taskNode].map((node) => ({
    ...node,
    title,
    status,
    detail,
    outputs: { ...node.outputs, ...outputs },
    ...action,
  }));
}

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

const taskEvidenceKeys = [
  "task_id",
  "task_status",
  "task_title",
  "task_type",
  "task_progress_detail",
  "task_error_message",
  "task_updated_at",
  "result_file_path",
] as const;

function reconciledTaskOutputs(outputs: Record<string, unknown> | undefined) {
  return Object.fromEntries(
    taskEvidenceKeys
      .filter((key) => outputs && key in outputs)
      .map((key) => [key, outputs?.[key]]),
  );
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
      outputs: {
        ...node.outputs,
        ...reconciledTaskOutputs(evidence.node.outputs),
      },
    };
  });
}
