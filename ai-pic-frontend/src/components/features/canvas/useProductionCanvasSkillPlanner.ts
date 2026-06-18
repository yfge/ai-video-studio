import { useState } from "react";
import { productionCanvasAPI } from "@/utils/api/endpoints";
import type {
  ProductionCanvasPlanNode,
  ProductionCanvasPlanResponse,
  ProductionCanvasSkillExecuteResponse,
  ProductionCanvasSkillResult,
} from "@/utils/api/types";
import type { ProductionCanvasNode } from "./productionCanvasModel";

function runOutputs(response: ProductionCanvasPlanResponse) {
  return {
    ...(response.run_id ? { canvas_run_id: response.run_id } : {}),
    ...(response.task_id ? { canvas_task_id: response.task_id } : {}),
  };
}

function toCanvasNode(
  node: ProductionCanvasPlanNode,
  response: ProductionCanvasPlanResponse,
): ProductionCanvasNode {
  return {
    id: node.id,
    label: node.label,
    title: node.title,
    status: node.status,
    x: node.x,
    y: node.y,
    width: node.width,
    height: node.height,
    kind: node.kind || "skill_result",
    skill: node.skill,
    detail: node.detail,
    outputs: { ...node.outputs, ...runOutputs(response) },
    reuseTargets: node.reuse_targets,
    actionHref: node.action_href || undefined,
    actionLabel: node.action_label || undefined,
  };
}

function outputString(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  return typeof value === "string" && value.trim() ? value : undefined;
}

function outputNumber(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function firstOutputNumber(
  outputs: Record<string, unknown> | undefined,
  key: string,
) {
  const value = outputs?.[key];
  if (!Array.isArray(value)) return undefined;
  const first = value.find((item) => typeof item === "number");
  return typeof first === "number" ? first : undefined;
}

function taskOutputNumber(outputs: Record<string, unknown> | undefined) {
  return (
    outputNumber(outputs, "task_id") ??
    outputNumber(outputs, "dispatched_task_id") ??
    outputNumber(outputs, "canvas_task_id")
  );
}

function resultToNode(
  node: ProductionCanvasNode,
  result: ProductionCanvasSkillResult,
): ProductionCanvasNode {
  return {
    ...node,
    label: result.label,
    title: result.title,
    status: result.status,
    detail: result.detail,
    outputs: { ...node.outputs, ...result.outputs },
    reuseTargets: result.reuse_targets,
  };
}

function resultToTaskNode(
  node: ProductionCanvasNode,
  result: ProductionCanvasSkillResult,
  response: ProductionCanvasSkillExecuteResponse,
): ProductionCanvasNode | null {
  const taskId = response.task_id ?? outputNumber(result.outputs, "dispatched_task_id");
  if (!taskId) return null;
  return {
    id: `${node.id}-task-${taskId}`,
    label: `Task #${taskId}`,
    title: result.title,
    status: result.status,
    x: node.x + 36,
    y: node.y + 112,
    width: Math.max(220, node.width),
    kind: "note",
    detail: result.detail,
    outputs: {
      skill: result.skill,
      task_id: taskId,
      task_status: response.task_status,
      ...result.outputs,
    },
    reuseTargets: result.reuse_targets,
    actionHref: "/tasks",
    actionLabel: "查看任务",
  };
}

export function useProductionCanvasSkillPlanner({
  onNodesCreated,
}: {
  onNodesCreated: (nodes: ProductionCanvasNode[]) => void;
}) {
  const [prompt, setPrompt] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [executingNodeId, setExecutingNodeId] = useState<string | null>(null);
  const [executionError, setExecutionError] = useState<string | null>(null);

  const createFromPrompt = async () => {
    const trimmed = prompt.trim();
    if (!trimmed || running) return;
    setRunning(true);
    setError(null);
    try {
      const response = await productionCanvasAPI.createPlan({ prompt: trimmed });
      if (!response.success || !response.data) {
        setError(response.error || "整体创建失败");
        return;
      }
      const plan = response.data;
      onNodesCreated(plan.nodes.map((node) => toCanvasNode(node, plan)));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  };

  const executeSkillNode = async (node: ProductionCanvasNode) => {
    if (!node.skill || executingNodeId) return;
    setExecutingNodeId(node.id);
    setExecutionError(null);
    try {
      const response = await productionCanvasAPI.executeSkill({
        prompt: prompt.trim() || outputString(node.outputs, "prompt") || node.title,
        skill: node.skill,
        run_id: outputString(node.outputs, "canvas_run_id"),
        episode_id: outputNumber(node.outputs, "episode_id"),
        script_id: outputNumber(node.outputs, "script_id"),
        task_id: taskOutputNumber(node.outputs),
        virtual_ip_id: firstOutputNumber(node.outputs, "virtual_ip_ids"),
        environment_id: firstOutputNumber(node.outputs, "environment_ids"),
      });
      if (!response.success || !response.data) {
        setExecutionError(response.error || "Skill 执行失败");
        return;
      }
      const skillNode = resultToNode(node, response.data.skill_result);
      const taskNode = resultToTaskNode(
        node,
        response.data.skill_result,
        response.data,
      );
      onNodesCreated(taskNode ? [skillNode, taskNode] : [skillNode]);
    } catch (err) {
      setExecutionError(err instanceof Error ? err.message : String(err));
    } finally {
      setExecutingNodeId(null);
    }
  };

  return {
    createFromPrompt,
    error,
    executeSkillNode,
    executingNodeId,
    executionError,
    prompt,
    running,
    setPrompt,
  };
}
