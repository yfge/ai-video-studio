import { useState } from "react";
import { taskAPI } from "@/utils/api/endpoints";
import type { Task } from "@/utils/api/types";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import {
  productionCanvasTaskStatusLabel,
  taskOutputNumber,
} from "./productionCanvasSkillNodes";

const TASK_SUMMARY_SYNC_ID = "__task-summary__";

function canvasStatusFromTask(
  status: Task["status"],
): ProductionCanvasNode["status"] {
  if (status === "failed" || status === "cancelled") return "blocked";
  if (status === "completed") return "review";
  return "running";
}

function taskDetail(task: Task) {
  const parts = [
    `任务 #${task.id} 当前状态 ${productionCanvasTaskStatusLabel(task.status)}`,
  ];
  if (task.progress_detail) parts.push(`进度：${task.progress_detail}`);
  if (task.error_message) parts.push(`错误：${task.error_message}`);
  return parts.join("；");
}

function taskNodePatch(task: Task): Partial<ProductionCanvasNode> {
  return {
    title: task.title,
    status: canvasStatusFromTask(task.status),
    detail: taskDetail(task),
    outputs: {
      task_id: task.id,
      task_status: task.status,
      task_title: task.title,
      task_type: task.task_type,
      task_progress_detail: task.progress_detail,
      task_error_message: task.error_message,
      task_updated_at: task.updated_at,
    },
    actionHref: `/tasks?task_id=${task.id}`,
    actionLabel: "查看任务",
  };
}

function taskRefreshErrorPatch(
  taskId: number,
  message: string,
): Partial<ProductionCanvasNode> {
  return {
    status: "blocked",
    detail: `任务 #${taskId} 刷新失败：${message}`,
    outputs: {
      task_status: "blocked",
      task_error_message: message,
    },
  };
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

export function useProductionCanvasTaskSync({
  onNodeUpdated,
}: {
  onNodeUpdated: (nodeId: string, patch: Partial<ProductionCanvasNode>) => void;
}) {
  const [syncingNodeId, setSyncingNodeId] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<{
    message: string;
    nodeId: string;
  } | null>(null);

  const refreshTaskNode = async (node: ProductionCanvasNode) => {
    const taskId = taskOutputNumber(node.outputs);
    if (!taskId || syncingNodeId) return;
    setSyncingNodeId(node.id);
    setSyncError(null);
    try {
      const response = await taskAPI.getTask(String(taskId));
      if (!response.success || !response.data) {
        throw new Error(response.error || `任务 #${taskId} 刷新失败`);
      }
      onNodeUpdated(node.id, taskNodePatch(response.data));
    } catch (error) {
      const message = errorMessage(error);
      onNodeUpdated(node.id, taskRefreshErrorPatch(taskId, message));
      setSyncError({
        message,
        nodeId: node.id,
      });
    } finally {
      setSyncingNodeId(null);
    }
  };

  const refreshTaskNodes = async (nodes: ProductionCanvasNode[]) => {
    const taskNodes = nodes.filter((node) => taskOutputNumber(node.outputs));
    if (!taskNodes.length || syncingNodeId) return;
    setSyncingNodeId(TASK_SUMMARY_SYNC_ID);
    setSyncError(null);
    let firstError: string | null = null;
    try {
      for (const node of taskNodes) {
        const taskId = taskOutputNumber(node.outputs);
        if (!taskId) continue;
        try {
          const response = await taskAPI.getTask(String(taskId));
          if (!response.success || !response.data) {
            throw new Error(response.error || `任务 #${taskId} 刷新失败`);
          }
          onNodeUpdated(node.id, taskNodePatch(response.data));
        } catch (error) {
          const message = errorMessage(error);
          onNodeUpdated(node.id, taskRefreshErrorPatch(taskId, message));
          firstError ??= message;
        }
      }
      if (firstError) {
        setSyncError({ message: firstError, nodeId: TASK_SUMMARY_SYNC_ID });
      }
    } finally {
      setSyncingNodeId(null);
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
