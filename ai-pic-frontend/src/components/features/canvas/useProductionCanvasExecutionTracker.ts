import { useRef } from "react";
import { useGenerationTaskTracker } from "@/hooks/useGenerationTaskTracker";
import {
  productionCanvasExecutionFailure,
  productionCanvasExecutionFromTask,
  type TrackedProductionCanvasExecution,
} from "./productionCanvasExecutionTracking";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { taskOutputNumber } from "./productionCanvasSkillNodes";

export function useProductionCanvasExecutionTracker({
  maxPollMs,
  onNodesCreated,
  pollIntervalMs,
}: {
  maxPollMs?: number;
  onNodesCreated: (nodes: ProductionCanvasNode[]) => void;
  pollIntervalMs?: number;
}) {
  const trackedExecutions = useRef(
    new Map<string, TrackedProductionCanvasExecution>(),
  );
  const taskTracker = useGenerationTaskTracker<string>({
    labels: (nodeId) =>
      trackedExecutions.current.get(nodeId)?.skillNode.label || "画布任务",
    maxPollMs,
    pollIntervalMs,
    onCompleted: (nodeId, _taskId, task) => {
      const execution = trackedExecutions.current.get(nodeId);
      if (!execution || !task) return;
      trackedExecutions.current.delete(nodeId);
      onNodesCreated(productionCanvasExecutionFromTask(execution, task));
    },
    onFailed: (nodeId, taskId, error) => {
      const execution = trackedExecutions.current.get(nodeId);
      if (!execution) return;
      trackedExecutions.current.delete(nodeId);
      onNodesCreated(
        productionCanvasExecutionFailure(execution, taskId, error),
      );
    },
  });

  return (
    sourceNode: ProductionCanvasNode,
    resultNodes: ProductionCanvasNode[],
  ) => {
    onNodesCreated(resultNodes);
    const skillNode = resultNodes.find((node) => node.id === sourceNode.id);
    const taskNode = resultNodes.find(
      (node) => node.kind === "note" && taskOutputNumber(node.outputs),
    );
    const taskId = taskOutputNumber(taskNode?.outputs);
    if (!skillNode || !taskNode || !taskId) return;
    trackedExecutions.current.set(sourceNode.id, { skillNode, taskNode });
    taskTracker.track(sourceNode.id, taskId);
  };
}
