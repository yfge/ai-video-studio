import type {
  ProductionCanvasResolvedContext,
  TimelineRenderJobResponse,
} from "@/utils/api/types";
import { productionCanvasContextOutputPatch } from "./productionCanvasContextMerge";
import { productionCanvasResolvedContextFromOutputs } from "./productionCanvasContextMerge";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import {
  isScopedProductionCanvasMediaNode,
  productionCanvasSharedContextForNode,
} from "./productionCanvasScopedContext";

export {
  productionCanvasExecutionFromTask,
  productionCanvasExecutionProgress,
} from "./productionCanvasTaskExecutionResult";

export type TrackedProductionCanvasExecution = {
  contextFingerprint?: string;
  operationEpoch?: number;
  runId?: string | null;
  skillNode: ProductionCanvasNode;
  taskNode: ProductionCanvasNode;
};

export function productionCanvasExecutionContextIsCurrent(
  execution: TrackedProductionCanvasExecution,
  contextFingerprint?: string,
) {
  return (
    isScopedProductionCanvasMediaNode(execution.skillNode) ||
    !execution.contextFingerprint ||
    execution.contextFingerprint === contextFingerprint
  );
}

export function normalizedProductionCanvasRunId(runId?: string | null) {
  return runId?.trim() || null;
}

export function productionCanvasExecutionBelongsToRun(
  execution: TrackedProductionCanvasExecution,
  runId: string | null,
  operationEpoch?: number,
) {
  return (
    (execution.runId || null) === runId &&
    (operationEpoch === undefined ||
      execution.operationEpoch === undefined ||
      execution.operationEpoch === operationEpoch)
  );
}

export function productionCanvasExecutionSharedContext(
  sourceNode: ProductionCanvasNode,
  resultNodes: ProductionCanvasNode[],
  resolvedContext?: ProductionCanvasResolvedContext,
) {
  const resultNode = resultNodes.find((node) => node.id === sourceNode.id);
  const context =
    resolvedContext ||
    productionCanvasResolvedContextFromOutputs(resultNode?.outputs);
  return productionCanvasSharedContextForNode(sourceNode, context);
}

function renderOutputUrl(job: TimelineRenderJobResponse) {
  return job.output_asset?.file_url || job.output_asset?.file_path;
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
    outputs: {
      ...node.outputs,
      ...productionCanvasContextOutputPatch(node.outputs, outputs),
      ...outputs,
    },
    ...action,
  }));
}

export {
  productionCanvasExecutionFailure,
  productionCanvasExecutionStale,
  productionCanvasRenderTimeout,
} from "./productionCanvasExecutionTermination";

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
  "task_prompt",
  "task_description",
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
        node.status === "stale" || node.status === "approved"
          ? node.status
          : evidence.taskStatus === "completed"
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
