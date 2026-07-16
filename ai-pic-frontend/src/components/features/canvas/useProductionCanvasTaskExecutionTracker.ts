import type { MutableRefObject } from "react";
import { useGenerationTaskTracker } from "@/hooks/useGenerationTaskTracker";
import type { ProductionCanvasResolvedContext } from "@/utils/api/types";
import {
  productionCanvasExecutionProgress,
  productionCanvasExecutionBelongsToRun,
  productionCanvasExecutionContextIsCurrent,
  productionCanvasExecutionFailure,
  productionCanvasExecutionFromTask,
  productionCanvasExecutionStale,
  type TrackedProductionCanvasExecution,
} from "./productionCanvasExecutionTracking";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { productionCanvasSharedContextForNode } from "./productionCanvasScopedContext";
import { taskOutputNumber } from "./productionCanvasSkillNodes";
import { resolveProductionCanvasTaskResultContext } from "./productionCanvasTaskResultContext";

export function useProductionCanvasTaskExecutionTracker({
  activeRunIdRef,
  activeOperationEpochRef,
  captureContextFingerprintRef,
  maxPollMs,
  mountedRef,
  onDomainContextResolvedRef,
  onNodesCreatedRef,
  pollIntervalMs,
  trackedExecutions,
}: {
  activeRunIdRef: MutableRefObject<string | null>;
  activeOperationEpochRef: MutableRefObject<number>;
  captureContextFingerprintRef: MutableRefObject<(() => string) | undefined>;
  maxPollMs: number;
  mountedRef: MutableRefObject<boolean>;
  onDomainContextResolvedRef: MutableRefObject<
    ((context: ProductionCanvasResolvedContext) => void) | undefined
  >;
  onNodesCreatedRef: MutableRefObject<
    (
      nodes: ProductionCanvasNode[],
      resolvedContext?: ProductionCanvasResolvedContext,
    ) => void
  >;
  pollIntervalMs: number;
  trackedExecutions: MutableRefObject<
    Map<string, TrackedProductionCanvasExecution>
  >;
}) {
  const currentExecution = (nodeId: string, taskId: number) => {
    const execution = trackedExecutions.current.get(nodeId);
    return execution &&
      taskOutputNumber(execution.taskNode.outputs) === taskId &&
      productionCanvasExecutionBelongsToRun(
        execution,
        activeRunIdRef.current,
        activeOperationEpochRef.current,
      )
      ? execution
      : undefined;
  };
  const detachStaleExecution = (
    nodeId: string,
    execution: TrackedProductionCanvasExecution,
  ) => {
    if (
      productionCanvasExecutionContextIsCurrent(
        execution,
        captureContextFingerprintRef.current?.(),
      )
    ) {
      return false;
    }
    trackedExecutions.current.delete(nodeId);
    onNodesCreatedRef.current(productionCanvasExecutionStale(execution));
    return true;
  };
  const finishTerminalTask = (
    nodeId: string,
    taskId: number,
    status: "failed" | "cancelled" | "timeout",
    error: string | null,
  ) => {
    const execution = currentExecution(nodeId, taskId);
    if (!execution || detachStaleExecution(nodeId, execution)) return;
    trackedExecutions.current.delete(nodeId);
    onNodesCreatedRef.current(
      productionCanvasExecutionFailure(execution, taskId, error, status),
    );
    const sharedContext = productionCanvasSharedContextForNode(
      execution.skillNode,
      { task_id: taskId },
    );
    if (sharedContext) onDomainContextResolvedRef.current?.(sharedContext);
  };
  return useGenerationTaskTracker<string>({
    labels: (nodeId) =>
      trackedExecutions.current.get(nodeId)?.skillNode.label || "画布任务",
    maxPollMs,
    pollIntervalMs,
    onCompleted: async (nodeId, taskId, task) => {
      const execution = currentExecution(nodeId, taskId);
      if (!execution || !task || detachStaleExecution(nodeId, execution))
        return;
      const context = await resolveProductionCanvasTaskResultContext(task);
      if (
        !mountedRef.current ||
        trackedExecutions.current.get(nodeId) !== execution ||
        !currentExecution(nodeId, taskId) ||
        detachStaleExecution(nodeId, execution)
      ) {
        return;
      }
      trackedExecutions.current.delete(nodeId);
      const settledContext = { ...context, task_id: taskId };
      const sharedContext = productionCanvasSharedContextForNode(
        execution.skillNode,
        settledContext,
      );
      onNodesCreatedRef.current(
        productionCanvasExecutionFromTask(execution, task, context),
        sharedContext,
      );
      if (sharedContext) onDomainContextResolvedRef.current?.(settledContext);
    },
    onCancelled: (nodeId, taskId) =>
      finishTerminalTask(nodeId, taskId, "cancelled", "任务已取消"),
    onFailed: (nodeId, taskId, error) =>
      finishTerminalTask(nodeId, taskId, "failed", error),
    onProgress: (nodeId, taskId, task) => {
      const execution = currentExecution(nodeId, taskId);
      if (!execution || detachStaleExecution(nodeId, execution)) return;
      const previous = execution.taskNode.outputs || {};
      const visibleDetail =
        task.progress_detail || task.description || task.prompt || "";
      if (
        previous.task_status === task.status &&
        previous.task_progress_detail === task.progress_detail &&
        previous.task_description === task.description &&
        previous.task_prompt === task.prompt
      ) {
        return;
      }
      if (!visibleDetail && task.status === "pending") return;
      const [skillNode, taskNode] = productionCanvasExecutionProgress(
        execution,
        task,
      );
      trackedExecutions.current.set(nodeId, {
        ...execution,
        skillNode,
        taskNode,
      });
      onNodesCreatedRef.current([skillNode, taskNode]);
    },
    onTimeout: (nodeId, taskId) =>
      finishTerminalTask(nodeId, taskId, "timeout", "等待任务完成超时"),
  });
}
