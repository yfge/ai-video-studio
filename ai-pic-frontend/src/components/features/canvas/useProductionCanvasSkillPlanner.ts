import { useState } from "react";
import { productionCanvasAPI } from "@/utils/api/endpoints";
import {
  emptyProductionCanvasContext,
  productionCanvasContextOutputs,
  productionCanvasRequestContext,
  type ProductionCanvasContextKey,
} from "./productionCanvasContext";
import type { ProductionCanvasNode } from "./productionCanvasModel";
import { applyProductionCanvasContext } from "./productionCanvasState";
import { useProductionCanvasExecutionTracker } from "./useProductionCanvasExecutionTracker";
import {
  firstOutputNumber,
  outputBoolean,
  outputNumber,
  outputNumberArray,
  outputString,
  outputStringArray,
  productionCanvasPlanNodeToCanvasNode,
  productionCanvasSkillResultToNode,
  productionCanvasSkillResultToTaskNode,
  taskOutputNumber,
} from "./productionCanvasSkillNodes";

function hasMissingRequiredInputs(node: ProductionCanvasNode) {
  const requiredInputs = node.outputs?.required_inputs;
  return Array.isArray(requiredInputs) && requiredInputs.length > 0;
}

function isAutoExecutableNode(node: ProductionCanvasNode) {
  return Boolean(
    node.skill && node.status === "ready" && !hasMissingRequiredInputs(node),
  );
}

function upsertCanvasNodes(
  currentNodes: ProductionCanvasNode[],
  incomingNodes: ProductionCanvasNode[],
) {
  const incomingIds = new Set(incomingNodes.map((node) => node.id));
  return applyProductionCanvasContext([
    ...currentNodes.filter((node) => !incomingIds.has(node.id)),
    ...incomingNodes,
  ]);
}

export function useProductionCanvasSkillPlanner({
  currentRunId,
  onNodesCreated,
  onRunCreated,
  taskMaxPollMs,
  taskPollIntervalMs,
}: {
  currentRunId?: string | null;
  onNodesCreated: (nodes: ProductionCanvasNode[]) => void;
  onRunCreated?: (runId: string) => void;
  taskMaxPollMs?: number;
  taskPollIntervalMs?: number;
}) {
  const [prompt, setPrompt] = useState("");
  const [context, setContext] = useState(emptyProductionCanvasContext);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [executingNodeId, setExecutingNodeId] = useState<string | null>(null);
  const [executionError, setExecutionError] = useState<string | null>(null);
  const publishExecutionNodes = useProductionCanvasExecutionTracker({
    maxPollMs: taskMaxPollMs,
    onNodesCreated,
    pollIntervalMs: taskPollIntervalMs,
    runId: currentRunId,
  });

  const setContextValue = (key: ProductionCanvasContextKey, value: string) => {
    setContext((current) => ({ ...current, [key]: value }));
  };

  const executeSkillRequest = async (
    node: ProductionCanvasNode,
    fallbackPrompt?: string,
  ) => {
    const requestContext = productionCanvasRequestContext(
      fallbackPrompt ? emptyProductionCanvasContext : context,
    );
    const response = await productionCanvasAPI.executeSkill({
      prompt:
        fallbackPrompt ||
        prompt.trim() ||
        outputString(node.outputs, "prompt") ||
        node.title,
      skill: node.skill || "",
      run_id:
        (currentRunId || "").trim() ||
        outputString(node.outputs, "canvas_run_id"),
      reference_artifacts: outputStringArray(
        node.outputs,
        "reference_artifacts",
      ),
      frame_indexes: outputNumberArray(node.outputs, "frame_indexes"),
      model: outputString(node.outputs, "model"),
      aspect_ratio: outputString(node.outputs, "aspect_ratio"),
      require_reference_images: outputBoolean(
        node.outputs,
        "require_reference_images",
      ),
      duration: outputNumber(node.outputs, "duration"),
      fps: outputNumber(node.outputs, "fps"),
      resolution: outputString(node.outputs, "resolution"),
      ratio: outputString(node.outputs, "ratio"),
      camera_fixed: outputBoolean(node.outputs, "camera_fixed"),
      episode_id:
        requestContext.episode_id || outputNumber(node.outputs, "episode_id"),
      script_id:
        requestContext.script_id || outputNumber(node.outputs, "script_id"),
      task_id: requestContext.task_id || taskOutputNumber(node.outputs),
      virtual_ip_id:
        requestContext.virtual_ip_id ||
        firstOutputNumber(node.outputs, "virtual_ip_ids"),
      environment_id:
        requestContext.environment_id ||
        firstOutputNumber(node.outputs, "environment_ids"),
    });
    if (!response.success || !response.data) {
      throw new Error(response.error || "Skill 执行失败");
    }
    const skillNode = productionCanvasSkillResultToNode(
      node,
      response.data.skill_result,
    );
    const taskNode = productionCanvasSkillResultToTaskNode(
      node,
      response.data.skill_result,
      response.data,
    );
    return taskNode ? [skillNode, taskNode] : [skillNode];
  };

  const executeReadyNodes = async (
    initialNodes: ProductionCanvasNode[],
    fallbackPrompt: string,
  ) => {
    const attemptedNodeIds = new Set<string>();
    let workingNodes = initialNodes;
    while (true) {
      const node = workingNodes.find(
        (candidate) =>
          isAutoExecutableNode(candidate) &&
          !attemptedNodeIds.has(candidate.id),
      );
      if (!node) return;
      attemptedNodeIds.add(node.id);
      setExecutingNodeId(node.id);
      const resultNodes = await executeSkillRequest(node, fallbackPrompt);
      publishExecutionNodes(node, resultNodes);
      workingNodes = upsertCanvasNodes(workingNodes, resultNodes);
    }
  };

  const createFromPrompt = async () => {
    const trimmed = prompt.trim();
    if (!trimmed || running) return;
    setRunning(true);
    setError(null);
    setExecutionError(null);
    try {
      const requestContext = productionCanvasRequestContext(context);
      const response = await productionCanvasAPI.createPlan({
        prompt: trimmed,
        ...requestContext,
      });
      if (!response.success || !response.data) {
        setError(response.error || "整体创建失败");
        return;
      }
      const plan = response.data;
      if (plan.run_id) onRunCreated?.(plan.run_id);
      const contextOutputs = productionCanvasContextOutputs(requestContext);
      const createdNodes = plan.nodes.map((node) =>
        productionCanvasPlanNodeToCanvasNode(node, plan, contextOutputs),
      );
      onNodesCreated(createdNodes);
      await executeReadyNodes(createdNodes, trimmed);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setExecutingNodeId(null);
      setRunning(false);
    }
  };

  const executeSkillNode = async (node: ProductionCanvasNode) => {
    if (!node.skill || executingNodeId) return;
    setExecutingNodeId(node.id);
    setExecutionError(null);
    try {
      publishExecutionNodes(node, await executeSkillRequest(node));
    } catch (err) {
      setExecutionError(err instanceof Error ? err.message : String(err));
    } finally {
      setExecutingNodeId(null);
    }
  };

  return {
    context,
    createFromPrompt,
    error,
    executeSkillNode,
    executingNodeId,
    executionError,
    prompt,
    running,
    setContextValue,
    setPrompt,
  };
}
