import { useEffect, useRef, useState } from "react";
import { taskAPI } from "@/utils/api/endpoints";
import type { ProductionCanvasResolvedContext } from "@/utils/api/types";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { taskOutputNumber } from "./productionCanvasSkillNodes";
import { resolveProductionCanvasTaskResultContext } from "./productionCanvasTaskResultContext";
import { useProductionCanvasOperationRun } from "./useProductionCanvasOperationRun";
import type { ProductionCanvasStateIdentity } from "./productionCanvasStateIdentity";
import { productionCanvasSharedContextForNode } from "./productionCanvasScopedContext";
import {
  productionCanvasCurrentTaskSource,
  productionCanvasTaskNodePatch,
  productionCanvasTaskRefreshErrorPatch,
} from "./productionCanvasTaskRefresh";

const TASK_SUMMARY_SYNC_ID = "__task-summary__";

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

function taskNodeIsCurrent(
  node: ProductionCanvasNode,
  nodes: ProductionCanvasNode[],
  taskId: number,
) {
  if (!nodes.length) return true;
  const current = nodes.find((candidate) => candidate.id === node.id);
  return Boolean(current && taskOutputNumber(current.outputs) === taskId);
}

export function useProductionCanvasTaskSync({
  currentRunId,
  captureStateIdentity,
  getCurrentRunId,
  nodes = [],
  operationBlocked = false,
  onDomainContextResolved,
  onNodeUpdated,
}: {
  currentRunId?: string | null;
  captureStateIdentity?: () => ProductionCanvasStateIdentity;
  getCurrentRunId: () => string | null | undefined;
  nodes?: ProductionCanvasNode[];
  operationBlocked?: boolean;
  onDomainContextResolved?: (context: ProductionCanvasResolvedContext) => void;
  onNodeUpdated: (nodeId: string, patch: Partial<ProductionCanvasNode>) => void;
}) {
  const [syncingNodeId, setSyncingNodeId] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<{
    message: string;
    nodeId: string;
  } | null>(null);
  const runGuard = useProductionCanvasOperationRun(
    getCurrentRunId,
    captureStateIdentity,
  );
  const nodesRef = useRef(nodes);
  nodesRef.current = nodes;
  const activeIdentity = runGuard.current;

  useEffect(() => {
    setSyncingNodeId(null);
    setSyncError(null);
  }, [activeIdentity.epoch, activeIdentity.runId, currentRunId]);

  const refreshTaskNode = async (node: ProductionCanvasNode) => {
    const taskId = taskOutputNumber(node.outputs);
    if (!taskId || syncingNodeId || operationBlocked) return;
    const operationIdentity = runGuard.capture();
    setSyncingNodeId(node.id);
    setSyncError(null);
    try {
      const response = await taskAPI.getTask(String(taskId));
      if (!runGuard.isCurrent(operationIdentity)) return;
      if (!response.success || !response.data) {
        throw new Error(response.error || `任务 #${taskId} 刷新失败`);
      }
      const context = await resolveProductionCanvasTaskResultContext(
        response.data,
      );
      if (
        !runGuard.isCurrent(operationIdentity) ||
        !taskNodeIsCurrent(node, nodesRef.current, taskId)
      )
        return;
      onNodeUpdated(
        node.id,
        productionCanvasTaskNodePatch(node, response.data, context),
      );
      const source = productionCanvasCurrentTaskSource(
        node,
        nodesRef.current,
        taskId,
      );
      if (source && source.id !== node.id) {
        onNodeUpdated(
          source.id,
          productionCanvasTaskNodePatch(source, response.data, context),
        );
      }
      const sharedContext = source
        ? productionCanvasSharedContextForNode(source, {
            ...context,
            task_id: taskId,
          })
        : undefined;
      if (sharedContext) {
        onDomainContextResolved?.(sharedContext);
      }
    } catch (error) {
      if (
        !runGuard.isCurrent(operationIdentity) ||
        !taskNodeIsCurrent(node, nodesRef.current, taskId)
      )
        return;
      const message = errorMessage(error);
      onNodeUpdated(
        node.id,
        productionCanvasTaskRefreshErrorPatch(taskId, message),
      );
      setSyncError({
        message,
        nodeId: node.id,
      });
    } finally {
      if (runGuard.isCurrent(operationIdentity)) setSyncingNodeId(null);
    }
  };

  const refreshTaskNodes = async (nodes: ProductionCanvasNode[]) => {
    const taskNodes = nodes.filter((node) => taskOutputNumber(node.outputs));
    if (!taskNodes.length || syncingNodeId || operationBlocked) return;
    const operationIdentity = runGuard.capture();
    setSyncingNodeId(TASK_SUMMARY_SYNC_ID);
    setSyncError(null);
    let firstError: string | null = null;
    try {
      for (const node of taskNodes) {
        if (!runGuard.isCurrent(operationIdentity)) return;
        const taskId = taskOutputNumber(node.outputs);
        if (!taskId) continue;
        try {
          const response = await taskAPI.getTask(String(taskId));
          if (!runGuard.isCurrent(operationIdentity)) return;
          if (!response.success || !response.data) {
            throw new Error(response.error || `任务 #${taskId} 刷新失败`);
          }
          const context = await resolveProductionCanvasTaskResultContext(
            response.data,
          );
          if (
            !runGuard.isCurrent(operationIdentity) ||
            !taskNodeIsCurrent(node, nodesRef.current, taskId)
          )
            continue;
          onNodeUpdated(
            node.id,
            productionCanvasTaskNodePatch(node, response.data, context),
          );
          const source = productionCanvasCurrentTaskSource(
            node,
            nodesRef.current,
            taskId,
          );
          if (source && source.id !== node.id) {
            onNodeUpdated(
              source.id,
              productionCanvasTaskNodePatch(source, response.data, context),
            );
          }
          const sharedContext = source
            ? productionCanvasSharedContextForNode(source, {
                ...context,
                task_id: taskId,
              })
            : undefined;
          if (sharedContext) {
            onDomainContextResolved?.(sharedContext);
          }
        } catch (error) {
          if (!runGuard.isCurrent(operationIdentity)) return;
          if (!taskNodeIsCurrent(node, nodesRef.current, taskId)) continue;
          const message = errorMessage(error);
          onNodeUpdated(
            node.id,
            productionCanvasTaskRefreshErrorPatch(taskId, message),
          );
          firstError ??= message;
        }
      }
      if (firstError && runGuard.isCurrent(operationIdentity)) {
        setSyncError({ message: firstError, nodeId: TASK_SUMMARY_SYNC_ID });
      }
    } finally {
      if (runGuard.isCurrent(operationIdentity)) setSyncingNodeId(null);
    }
  };

  return {
    refreshTaskNodes,
    refreshTaskNode,
    syncError,
    syncSummaryError:
      syncError?.nodeId === TASK_SUMMARY_SYNC_ID ? syncError.message : null,
    syncingNodeId,
    syncingTaskSummary: syncingNodeId === TASK_SUMMARY_SYNC_ID,
  };
}
